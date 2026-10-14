"""Disaggregated fairness and performance diagnostics."""

from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.metrics import brier_score_loss, roc_auc_score


def _group_metrics(group: pd.DataFrame) -> pd.Series:
    approved = group["recommendation"].eq("APPROVE_RECOMMENDATION").astype(int)
    non_default = group["default_12m"].eq(0)
    default = ~non_default
    auc = (
        roc_auc_score(group["default_12m"], group["predicted_pd"])
        if group["default_12m"].nunique() > 1
        else float("nan")
    )
    return pd.Series(
        {
            "applications": len(group),
            "observed_default_rate": group["default_12m"].mean(),
            "average_predicted_pd": group["predicted_pd"].mean(),
            "approval_rate": approved.mean(),
            "good_applicant_approval_rate": approved[non_default].mean(),
            "defaulting_applicant_approval_rate": approved[default].mean(),
            "roc_auc": auc,
            "brier": brier_score_loss(group["default_12m"], group["predicted_pd"]),
        }
    )


def fairness_audit(
    scored_frame: pd.DataFrame, protected_attributes: list[str]
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Assess approval allocation and predictive performance by protected group."""
    required_columns = {"recommendation", "default_12m", "predicted_pd"}
    missing_columns = sorted(required_columns.difference(scored_frame.columns))
    if missing_columns:
        raise ValueError(f"Fairness audit is missing required columns: {missing_columns}")
    if scored_frame.empty:
        raise ValueError("Fairness audit requires at least one scored application")
    if not protected_attributes or len(protected_attributes) != len(set(protected_attributes)):
        raise ValueError("Protected attributes must be a non-empty list without duplicates")
    missing_attributes = sorted(set(protected_attributes).difference(scored_frame.columns))
    if missing_attributes:
        raise ValueError(f"Fairness audit is missing protected attributes: {missing_attributes}")

    predicted_pd = pd.to_numeric(scored_frame["predicted_pd"], errors="coerce")
    if (
        not np.isfinite(predicted_pd.to_numpy(dtype=float)).all()
        or not predicted_pd.between(0, 1).all()
    ):
        raise ValueError("predicted_pd must contain finite probabilities in [0, 1]")
    outcomes = pd.to_numeric(scored_frame["default_12m"], errors="coerce")
    if outcomes.isna().any() or not outcomes.isin([0, 1]).all():
        raise ValueError("default_12m must contain only binary 0/1 outcomes")
    for attribute in protected_attributes:
        labels = scored_frame[attribute]
        if labels.isna().any() or labels.astype(str).str.strip().eq("").any():
            raise ValueError(f"Protected attribute {attribute!r} contains missing or blank labels")

    scored_frame = scored_frame.assign(predicted_pd=predicted_pd, default_12m=outcomes.astype(int))
    details: list[pd.DataFrame] = []
    summaries: list[dict[str, float | str]] = []
    for attribute in protected_attributes:
        grouped = (
            scored_frame.groupby(attribute, observed=True)
            .apply(_group_metrics, include_groups=False)
            .reset_index()
            .rename(columns={attribute: "group"})
        )
        grouped.insert(0, "protected_attribute", attribute)
        details.append(grouped)
        demographic_parity_difference = float(
            grouped["approval_rate"].max() - grouped["approval_rate"].min()
        )
        equal_opportunity_difference = float(
            grouped["good_applicant_approval_rate"].max()
            - grouped["good_applicant_approval_rate"].min()
        )
        diagnostic_status = (
            "GOVERNANCE_REVIEW_REQUIRED"
            if max(demographic_parity_difference, equal_opportunity_difference) >= 0.10
            else "NO_MATERIAL_SIGNAL_AT_10PP_TRIAGE_LEVEL"
        )
        summaries.append(
            {
                "protected_attribute": attribute,
                "demographic_parity_difference": demographic_parity_difference,
                "equal_opportunity_difference": equal_opportunity_difference,
                "defaulting_approval_rate_difference": float(
                    grouped["defaulting_applicant_approval_rate"].max()
                    - grouped["defaulting_applicant_approval_rate"].min()
                ),
                "auc_range": float(grouped["roc_auc"].max() - grouped["roc_auc"].min()),
                "minimum_group_size": int(grouped["applications"].min()),
                "diagnostic_status": diagnostic_status,
                "interpretation": (
                    "The 10 percentage-point level is an internal triage signal, not a legal "
                    "fairness standard. Legal review, causal analysis and stakeholder governance "
                    "remain mandatory."
                ),
            }
        )
    return pd.concat(details, ignore_index=True), pd.DataFrame(summaries)
