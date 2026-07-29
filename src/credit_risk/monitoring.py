"""Population stability and model performance monitoring."""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd
from sklearn.metrics import brier_score_loss, roc_auc_score


def population_stability_index(
    reference: np.ndarray,
    current: np.ndarray,
    bins: int = 10,
) -> float:
    """Calculate PSI with quantile bins and numerical safeguards."""
    reference_values = np.asarray(reference, dtype=float)
    current_values = np.asarray(current, dtype=float)
    edges = np.unique(np.quantile(reference_values, np.linspace(0, 1, bins + 1)))
    if edges.size < 3:
        return 0.0
    edges[0] = -np.inf
    edges[-1] = np.inf
    reference_counts = np.histogram(reference_values, bins=edges)[0] / len(reference_values)
    current_counts = np.histogram(current_values, bins=edges)[0] / len(current_values)
    reference_counts = np.clip(reference_counts, 1e-6, None)
    current_counts = np.clip(current_counts, 1e-6, None)
    return float(
        np.sum((current_counts - reference_counts) * np.log(current_counts / reference_counts))
    )


def _status(value: float, warning: float, critical: float) -> str:
    if value >= critical:
        return "RED"
    if value >= warning:
        return "AMBER"
    return "GREEN"


def monitoring_report(
    scored_frame: pd.DataFrame,
    development_mask: pd.Series,
    validation_mask: pd.Series,
    config: dict[str, Any],
) -> pd.DataFrame:
    """Create monthly OOT monitoring with explicit alert thresholds."""
    thresholds = config["monitoring"]
    reference = scored_frame.loc[development_mask]
    validation = scored_frame.loc[validation_mask]
    baseline_auc = roc_auc_score(validation["default_12m"], validation["predicted_pd"])
    baseline_approval = validation["recommendation"].eq("APPROVE_RECOMMENDATION").mean()
    oot = scored_frame.loc[~development_mask & ~validation_mask].copy()
    oot["monitoring_month"] = oot["application_date"].dt.to_period("M").astype(str)
    rows: list[dict[str, Any]] = []
    for month, group in oot.groupby("monitoring_month", sort=True):
        auc = (
            roc_auc_score(group["default_12m"], group["predicted_pd"])
            if group["default_12m"].nunique() > 1
            else float("nan")
        )
        score_psi = population_stability_index(
            reference["predicted_pd"].to_numpy(), group["predicted_pd"].to_numpy()
        )
        approval_rate = group["recommendation"].eq("APPROVE_RECOMMENDATION").mean()
        auc_drop = max(0.0, baseline_auc - auc)
        approval_change = abs(approval_rate - baseline_approval)
        statuses = [
            _status(
                score_psi,
                thresholds["score_psi_warning"],
                thresholds["score_psi_critical"],
            ),
            _status(
                auc_drop,
                thresholds["auc_drop_warning"],
                thresholds["auc_drop_critical"],
            ),
            "AMBER" if approval_change >= thresholds["approval_rate_change_warning"] else "GREEN",
        ]
        overall = "RED" if "RED" in statuses else "AMBER" if "AMBER" in statuses else "GREEN"
        rows.append(
            {
                "monitoring_month": month,
                "applications": len(group),
                "observed_default_rate": group["default_12m"].mean(),
                "average_predicted_pd": group["predicted_pd"].mean(),
                "roc_auc": auc,
                "auc_drop_vs_validation": auc_drop,
                "brier": brier_score_loss(group["default_12m"], group["predicted_pd"]),
                "approval_rate": approval_rate,
                "approval_rate_change": approval_change,
                "score_psi": score_psi,
                "bureau_score_psi": population_stability_index(
                    reference["bureau_score"].to_numpy(), group["bureau_score"].to_numpy()
                ),
                "debt_to_income_psi": population_stability_index(
                    reference["debt_to_income"].to_numpy(), group["debt_to_income"].to_numpy()
                ),
                "alert_status": overall,
            }
        )
    return pd.DataFrame(rows)
