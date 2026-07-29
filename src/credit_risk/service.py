"""Artifact-backed scoring service without transport concerns."""

from __future__ import annotations

import re
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd

from credit_risk.config import load_config
from credit_risk.policy import pd_to_score, recommendation, risk_band


def _friendly_name(transformed_name: str) -> str:
    value = transformed_name.replace("num__", "").replace("cat__", "")
    categorical = [
        "employment_type",
        "housing_status",
        "income_verified",
        "channel",
        "region",
        "purpose",
    ]
    for feature in sorted(categorical, key=len, reverse=True):
        if value.startswith(f"{feature}_"):
            return f"{feature} = {value[len(feature) + 1 :]}"
    return value


def _reason_code(feature: str, direction: str) -> str:
    cleaned = re.sub(r"[^A-Z0-9]+", "_", feature.upper()).strip("_")[:36]
    return f"{direction}_{cleaned}"


@dataclass
class ScoringService:
    """Loads the governed champion and returns recommendation-only outputs."""

    root: Path
    model: Any
    shap_state: dict[str, Any]
    config: dict[str, Any]

    @classmethod
    def load(cls, root: str | Path) -> ScoringService:
        root_path = Path(root).resolve()
        model = joblib.load(root_path / "artifacts/model/champion_logistic_pipeline.joblib")
        shap_state = joblib.load(root_path / "artifacts/model/linear_shap_state.joblib")
        config = load_config(root_path / "config/project.yaml")
        return cls(root=root_path, model=model, shap_state=shap_state, config=config)

    def score(self, application: dict[str, Any], request_id: str | None = None) -> dict[str, Any]:
        frame = pd.DataFrame([application])
        probability = float(self.model.predict_proba(frame)[:, 1][0])
        policy = self.config["policy"]
        rec = recommendation(probability, policy)
        transformed = np.asarray(
            self.model.named_steps["preprocess"].transform(frame), dtype=float
        )[0]
        coefficients = self.model.named_steps["classifier"].coef_[0]
        contributions = (transformed - self.shap_state["background_mean"]) * coefficients
        order = np.argsort(contributions)[::-1]
        positive = [index for index in order if contributions[index] > 0][:4]
        if len(positive) < 4:
            positive.extend(
                [index for index in order if index not in positive][: 4 - len(positive)]
            )
        reasons = []
        for rank, index in enumerate(positive, start=1):
            feature = _friendly_name(str(self.shap_state["feature_names"][index]))
            contribution = float(contributions[index])
            direction = "RISK_UP" if contribution >= 0 else "RISK_DOWN"
            reasons.append(
                {
                    "rank": rank,
                    "code": _reason_code(feature, direction),
                    "feature": feature,
                    "contribution_log_odds": contribution,
                    "direction": direction,
                }
            )
        return {
            "request_id": request_id or str(uuid.uuid4()),
            "model_version": self.config["project"]["version"],
            "probability_of_default_12m": probability,
            "credit_score": int(pd_to_score(np.array([probability]), policy)[0]),
            "risk_band": risk_band(probability),
            "recommendation": rec,
            "human_review_required": rec in policy["mandatory_human_review"],
            "illustrative_expected_loss": (
                probability * policy["lgd_assumption"] * application["requested_amount"]
            ),
            "reason_codes": reasons,
            "scope_notice": (
                "Decision support only. This output is not a final lending decision or a "
                "legally sufficient adverse-action notice; authorized human review is required."
            ),
        }
