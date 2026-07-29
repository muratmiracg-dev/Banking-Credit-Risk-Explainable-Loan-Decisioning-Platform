"""Credit model validation metrics."""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    average_precision_score,
    brier_score_loss,
    confusion_matrix,
    log_loss,
    roc_auc_score,
    roc_curve,
)


def _safe_auc(y_true: np.ndarray, probability: np.ndarray) -> float:
    return float(roc_auc_score(y_true, probability)) if np.unique(y_true).size > 1 else float("nan")


def calibration_parameters(y_true: np.ndarray, probability: np.ndarray) -> tuple[float, float]:
    """Estimate calibration intercept and slope from predicted logits."""
    clipped = np.clip(probability, 1e-6, 1 - 1e-6)
    logit = np.log(clipped / (1 - clipped)).reshape(-1, 1)
    calibrator = LogisticRegression(C=1e6, solver="lbfgs", max_iter=1000)
    calibrator.fit(logit, y_true)
    return float(calibrator.intercept_[0]), float(calibrator.coef_[0, 0])


def evaluate_binary(
    y_true: np.ndarray | pd.Series,
    probability: np.ndarray,
    adverse_threshold: float = 0.22,
) -> dict[str, Any]:
    """Return discrimination, calibration and threshold diagnostics."""
    truth = np.asarray(y_true, dtype=int)
    probability = np.asarray(probability, dtype=float)
    prediction = (probability >= adverse_threshold).astype(int)
    auc = _safe_auc(truth, probability)
    fpr, tpr, _ = roc_curve(truth, probability)
    tn, fp, fn, tp = confusion_matrix(truth, prediction, labels=[0, 1]).ravel()
    intercept, slope = calibration_parameters(truth, probability)
    return {
        "observations": int(len(truth)),
        "defaults": int(truth.sum()),
        "default_rate": float(truth.mean()),
        "roc_auc": auc,
        "gini": float(2 * auc - 1),
        "pr_auc": float(average_precision_score(truth, probability)),
        "ks": float(np.max(tpr - fpr)),
        "brier": float(brier_score_loss(truth, probability)),
        "log_loss": float(log_loss(truth, probability)),
        "calibration_intercept": intercept,
        "calibration_slope": slope,
        "threshold": float(adverse_threshold),
        "sensitivity": float(tp / (tp + fn)) if tp + fn else 0.0,
        "specificity": float(tn / (tn + fp)) if tn + fp else 0.0,
        "precision": float(tp / (tp + fp)) if tp + fp else 0.0,
    }


def build_decile_table(
    identifiers: pd.Series,
    y_true: pd.Series,
    probability: np.ndarray,
) -> pd.DataFrame:
    """Create a descending-risk decile table with cumulative capture."""
    working = pd.DataFrame(
        {
            "application_id": identifiers.to_numpy(),
            "actual_default": y_true.to_numpy(),
            "predicted_pd": probability,
        }
    ).sort_values("predicted_pd", ascending=False)
    working["risk_decile"] = pd.qcut(np.arange(len(working)), q=10, labels=np.arange(1, 11)).astype(
        int
    )
    grouped = (
        working.groupby("risk_decile", observed=True)
        .agg(
            applications=("application_id", "count"),
            defaults=("actual_default", "sum"),
            observed_default_rate=("actual_default", "mean"),
            average_predicted_pd=("predicted_pd", "mean"),
            minimum_pd=("predicted_pd", "min"),
            maximum_pd=("predicted_pd", "max"),
        )
        .reset_index()
    )
    grouped["cumulative_default_capture"] = grouped["defaults"].cumsum() / grouped["defaults"].sum()
    grouped["lift_vs_portfolio"] = (
        grouped["observed_default_rate"] / working["actual_default"].mean()
    )
    return grouped
