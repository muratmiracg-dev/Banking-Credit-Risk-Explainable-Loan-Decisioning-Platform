"""Temporal model development and challenger comparison."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import HistGradientBoostingClassifier, RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, OrdinalEncoder, StandardScaler

from credit_risk.data import CATEGORICAL_FEATURES, NUMERIC_FEATURES, TARGET
from credit_risk.metrics import evaluate_binary


@dataclass
class ModelBundle:
    """Fitted models and validation evidence."""

    champion_name: str
    champion: Pipeline
    models: dict[str, Pipeline]
    comparison: pd.DataFrame
    validation_metrics: dict[str, dict[str, Any]]


def _logistic_pipeline(seed: int) -> Pipeline:
    preprocess = ColumnTransformer(
        [
            (
                "num",
                Pipeline(
                    [
                        ("imputer", SimpleImputer(strategy="median")),
                        ("scaler", StandardScaler()),
                    ]
                ),
                NUMERIC_FEATURES,
            ),
            (
                "cat",
                Pipeline(
                    [
                        ("imputer", SimpleImputer(strategy="most_frequent")),
                        (
                            "encoder",
                            OneHotEncoder(
                                handle_unknown="ignore",
                                sparse_output=False,
                                min_frequency=10,
                            ),
                        ),
                    ]
                ),
                CATEGORICAL_FEATURES,
            ),
        ],
        verbose_feature_names_out=True,
    )
    return Pipeline(
        [
            ("preprocess", preprocess),
            (
                "classifier",
                LogisticRegression(
                    C=0.8,
                    solver="lbfgs",
                    max_iter=1500,
                    random_state=seed,
                ),
            ),
        ]
    )


def _tree_preprocess() -> ColumnTransformer:
    return ColumnTransformer(
        [
            (
                "num",
                SimpleImputer(strategy="median", add_indicator=True),
                NUMERIC_FEATURES,
            ),
            (
                "cat",
                Pipeline(
                    [
                        ("imputer", SimpleImputer(strategy="most_frequent")),
                        (
                            "encoder",
                            OrdinalEncoder(
                                handle_unknown="use_encoded_value",
                                unknown_value=-1,
                            ),
                        ),
                    ]
                ),
                CATEGORICAL_FEATURES,
            ),
        ],
        verbose_feature_names_out=True,
    )


def _histogram_gradient_boosting(seed: int) -> Pipeline:
    return Pipeline(
        [
            ("preprocess", _tree_preprocess()),
            (
                "classifier",
                HistGradientBoostingClassifier(
                    learning_rate=0.055,
                    max_iter=180,
                    max_leaf_nodes=21,
                    min_samples_leaf=55,
                    l2_regularization=1.5,
                    random_state=seed,
                ),
            ),
        ]
    )


def _random_forest(seed: int) -> Pipeline:
    return Pipeline(
        [
            ("preprocess", _tree_preprocess()),
            (
                "classifier",
                RandomForestClassifier(
                    n_estimators=180,
                    max_depth=11,
                    min_samples_leaf=35,
                    max_features=0.7,
                    n_jobs=-1,
                    random_state=seed,
                ),
            ),
        ]
    )


def build_models(seed: int) -> dict[str, Pipeline]:
    """Create champion candidate and two challengers."""
    return {
        "logistic_regression": _logistic_pipeline(seed),
        "histogram_gradient_boosting": _histogram_gradient_boosting(seed),
        "random_forest": _random_forest(seed),
    }


def train_and_compare(
    frame: pd.DataFrame,
    split: pd.Series,
    config: dict[str, Any],
) -> ModelBundle:
    """Fit temporal development models and compare on the holdout validation window."""
    features = NUMERIC_FEATURES + CATEGORICAL_FEATURES
    development = split.eq("development")
    validation = split.eq("validation")
    seed = int(config["data"]["seed"])
    models = build_models(seed)
    validation_metrics: dict[str, dict[str, Any]] = {}
    comparison_rows: list[dict[str, Any]] = []

    for name, model in models.items():
        model.fit(frame.loc[development, features], frame.loc[development, TARGET])
        probability = model.predict_proba(frame.loc[validation, features])[:, 1]
        metrics = evaluate_binary(
            frame.loc[validation, TARGET].to_numpy(),
            probability,
            adverse_threshold=config["policy"]["refer_max_pd"],
        )
        validation_metrics[name] = metrics
        comparison_rows.append(
            {
                "model": name,
                "roc_auc": metrics["roc_auc"],
                "gini": metrics["gini"],
                "pr_auc": metrics["pr_auc"],
                "ks": metrics["ks"],
                "brier": metrics["brier"],
                "calibration_intercept": metrics["calibration_intercept"],
                "calibration_slope": metrics["calibration_slope"],
                "explainability": (
                    "Exact additive Linear SHAP"
                    if name == "logistic_regression"
                    else "Challenger diagnostics only"
                ),
                "deployment_status": (
                    "CHAMPION" if name == config["model"]["champion"] else "CHALLENGER"
                ),
            }
        )

    champion_name = config["model"]["champion"]
    champion_metrics = validation_metrics[champion_name]
    slope_low, slope_high = config["model"]["calibration_slope_range"]
    if champion_metrics["roc_auc"] < config["model"]["minimum_oot_auc"]:
        raise RuntimeError("Champion failed the minimum validation AUC gate.")
    if not slope_low <= champion_metrics["calibration_slope"] <= slope_high:
        raise RuntimeError("Champion failed the calibration slope gate.")
    comparison = pd.DataFrame(comparison_rows).sort_values(
        ["deployment_status", "roc_auc"], ascending=[True, False]
    )
    return ModelBundle(
        champion_name=champion_name,
        champion=models[champion_name],
        models=models,
        comparison=comparison,
        validation_metrics=validation_metrics,
    )


def score_model(model: Pipeline, frame: pd.DataFrame) -> np.ndarray:
    """Predict default probabilities using only approved application-time features."""
    return model.predict_proba(frame[NUMERIC_FEATURES + CATEGORICAL_FEATURES])[:, 1]
