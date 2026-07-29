"""Exact additive Linear SHAP explanations for the logistic champion."""

from __future__ import annotations

import re
from dataclasses import dataclass

import numpy as np
import pandas as pd
from sklearn.pipeline import Pipeline

from credit_risk.data import CATEGORICAL_FEATURES, NUMERIC_FEATURES


@dataclass
class LinearShapResult:
    """Global and local explanation artifacts."""

    global_importance: pd.DataFrame
    local_reasons: pd.DataFrame
    expected_log_odds: float
    max_additivity_error: float


def _friendly_name(transformed_name: str) -> str:
    name = transformed_name.replace("num__", "").replace("cat__", "")
    for feature in sorted(CATEGORICAL_FEATURES, key=len, reverse=True):
        prefix = f"{feature}_"
        if name.startswith(prefix):
            value = name[len(prefix) :]
            return f"{feature} = {value}"
    return name


def _reason_code(name: str, direction: str) -> str:
    cleaned = re.sub(r"[^A-Z0-9]+", "_", name.upper()).strip("_")[:36]
    return f"{direction}_{cleaned}"


def explain_logistic(
    model: Pipeline,
    development_frame: pd.DataFrame,
    scored_frame: pd.DataFrame,
    probability: np.ndarray,
    top_n: int = 4,
) -> LinearShapResult:
    """Compute exact interventional Linear SHAP values in log-odds space.

    For a linear model under the feature-independence assumption:
    phi_j = beta_j * (x_j - E[x_j]).
    """
    features = NUMERIC_FEATURES + CATEGORICAL_FEATURES
    preprocess = model.named_steps["preprocess"]
    classifier = model.named_steps["classifier"]
    background = np.asarray(preprocess.transform(development_frame[features]), dtype=float)
    transformed = np.asarray(preprocess.transform(scored_frame[features]), dtype=float)
    feature_names = preprocess.get_feature_names_out()
    coefficients = classifier.coef_[0]
    background_mean = background.mean(axis=0)
    shap_values = (transformed - background_mean) * coefficients
    expected_log_odds = float(classifier.intercept_[0] + background_mean @ coefficients)
    reconstructed = expected_log_odds + shap_values.sum(axis=1)
    clipped = np.clip(probability, 1e-8, 1 - 1e-8)
    model_log_odds = np.log(clipped / (1 - clipped))
    max_error = float(np.max(np.abs(reconstructed - model_log_odds)))

    global_importance = (
        pd.DataFrame(
            {
                "transformed_feature": feature_names,
                "feature": [_friendly_name(name) for name in feature_names],
                "mean_abs_shap_log_odds": np.abs(shap_values).mean(axis=0),
                "mean_shap_log_odds": shap_values.mean(axis=0),
                "coefficient": coefficients,
            }
        )
        .sort_values("mean_abs_shap_log_odds", ascending=False)
        .reset_index(drop=True)
    )
    rows: list[dict[str, object]] = []
    for row_position, (application_id, pd_value) in enumerate(
        zip(scored_frame["application_id"], probability, strict=True)
    ):
        order = np.argsort(shap_values[row_position])[::-1]
        positive = [idx for idx in order if shap_values[row_position, idx] > 0][:top_n]
        if len(positive) < top_n:
            positive.extend([idx for idx in order if idx not in positive][: top_n - len(positive)])
        for rank, index in enumerate(positive, start=1):
            feature = _friendly_name(str(feature_names[index]))
            value = float(shap_values[row_position, index])
            direction = "RISK_UP" if value >= 0 else "RISK_DOWN"
            rows.append(
                {
                    "application_id": application_id,
                    "predicted_pd": float(pd_value),
                    "reason_rank": rank,
                    "reason_code": _reason_code(feature, direction),
                    "feature": feature,
                    "shap_log_odds": value,
                    "direction": direction,
                    "explanation_scope": "Model contribution; not a legally sufficient adverse-action notice",
                }
            )
    return LinearShapResult(
        global_importance=global_importance,
        local_reasons=pd.DataFrame(rows),
        expected_log_odds=expected_log_odds,
        max_additivity_error=max_error,
    )
