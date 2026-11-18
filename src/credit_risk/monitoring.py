"""Population stability and model performance monitoring."""

from __future__ import annotations

import numbers
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
    raw_reference = np.asarray(reference, dtype=object)
    raw_current = np.asarray(current, dtype=object)
    if any(
        values.ndim != 1
        or any(
            isinstance(value, (bool, np.bool_)) or not isinstance(value, numbers.Real)
            for value in values
        )
        for values in (raw_reference, raw_current)
    ):
        raise ValueError("PSI inputs must be one-dimensional numeric values, not booleans")
    reference_values = np.asarray(raw_reference, dtype=float)
    current_values = np.asarray(raw_current, dtype=float)
    if isinstance(bins, bool) or not isinstance(bins, int) or bins < 2:
        raise ValueError("bins must be an integer greater than or equal to 2")
    if reference_values.size == 0 or current_values.size == 0:
        raise ValueError("PSI requires non-empty reference and current samples")
    if not np.isfinite(reference_values).all() or not np.isfinite(current_values).all():
        raise ValueError("PSI samples must contain only finite values")
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


def calibration_in_the_large(outcomes: np.ndarray, predicted_pd: np.ndarray) -> dict[str, float]:
    """Compare observed defaults with the defaults the model expected.

    ``ae_ratio`` is actual-to-expected defaults. ``z_score`` is the normal approximation
    to the binomial test, (observed - expected) / sqrt(sum p(1 - p)), so small cohorts
    are not escalated on noise alone.
    """
    observed = np.asarray(outcomes, dtype=float)
    expected_pd = np.asarray(predicted_pd, dtype=float)
    if observed.size == 0 or observed.size != expected_pd.size:
        raise ValueError("calibration inputs must be non-empty and aligned")
    expected = float(expected_pd.sum())
    variance = float((expected_pd * (1 - expected_pd)).sum())
    observed_defaults = float(observed.sum())
    return {
        "observed_defaults": observed_defaults,
        "expected_defaults": expected,
        "ae_ratio": observed_defaults / expected if expected > 0 else float("nan"),
        "z_score": (observed_defaults - expected) / np.sqrt(variance)
        if variance > 0
        else float("nan"),
    }


def _calibration_status(calibration: dict[str, float], thresholds: dict[str, Any]) -> str:
    deviation = abs(calibration["ae_ratio"] - 1.0)
    if (
        not np.isfinite(deviation)
        or abs(calibration["z_score"]) < thresholds["calibration_z_minimum"]
    ):
        return "GREEN"
    return _status(
        deviation,
        thresholds["calibration_ae_warning"],
        thresholds["calibration_ae_critical"],
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
    required = {
        "application_date",
        "default_12m",
        "predicted_pd",
        "recommendation",
        "bureau_score",
        "debt_to_income",
    }
    missing = sorted(required - set(scored_frame.columns))
    if missing:
        raise ValueError("monitoring frame is missing required columns: " + ", ".join(missing))
    if (
        scored_frame.empty
        or len(development_mask) != len(scored_frame)
        or len(validation_mask) != len(scored_frame)
    ):
        raise ValueError("monitoring masks must be aligned with a non-empty scored frame")
    if development_mask.dtype != bool or validation_mask.dtype != bool:
        raise ValueError("monitoring masks must be boolean")
    if (
        (development_mask & validation_mask).any()
        or not development_mask.any()
        or not validation_mask.any()
    ):
        raise ValueError("development and validation masks must be non-empty and disjoint")
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
        # A month without both outcomes has no AUC; report the drop as unknown rather
        # than as "no drop" (max(0.0, nan) evaluated to 0.0).
        auc_drop = max(0.0, baseline_auc - auc) if np.isfinite(auc) else float("nan")
        approval_change = abs(approval_rate - baseline_approval)
        calibration = calibration_in_the_large(
            group["default_12m"].to_numpy(), group["predicted_pd"].to_numpy()
        )
        calibration_status = _calibration_status(calibration, thresholds)
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
            )
            if np.isfinite(auc_drop)
            else "GREEN",
            "AMBER" if approval_change >= thresholds["approval_rate_change_warning"] else "GREEN",
            calibration_status,
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
                "expected_defaults": calibration["expected_defaults"],
                "observed_defaults": calibration["observed_defaults"],
                "actual_to_expected_defaults": calibration["ae_ratio"],
                "calibration_z_score": calibration["z_score"],
                "calibration_status": calibration_status,
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
