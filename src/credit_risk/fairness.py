"""Disaggregated fairness and performance diagnostics."""

from __future__ import annotations

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
