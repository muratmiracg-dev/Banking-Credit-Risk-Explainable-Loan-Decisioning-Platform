"""Transparent decision-support policy."""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd


def pd_to_score(probability: np.ndarray, policy: dict[str, Any]) -> np.ndarray:
    """Map PD to a conventional 300-850 score scale."""
    pd_values = np.clip(np.asarray(probability, dtype=float), 1e-6, 1 - 1e-6)
    odds = pd_values / (1 - pd_values)
    anchor_odds = policy["score_anchor_pd"] / (1 - policy["score_anchor_pd"])
    factor = policy["points_to_double_odds"] / np.log(2)
    score = policy["score_anchor"] - factor * np.log(odds / anchor_odds)
    return np.clip(np.rint(score), 300, 850).astype(int)


def risk_band(probability: float) -> str:
    """Assign a stable A-F PD risk band."""
    if probability < 0.03:
        return "A"
    if probability < 0.06:
        return "B"
    if probability < 0.10:
        return "C"
    if probability < 0.15:
        return "D"
    if probability < 0.22:
        return "E"
    return "F"


def recommendation(probability: float, policy: dict[str, Any]) -> str:
    """Return a recommendation, never a legally operative lending decision."""
    if probability < policy["approve_max_pd"]:
        return "APPROVE_RECOMMENDATION"
    if probability < policy["refer_max_pd"]:
        return "REFER"
    return "DECLINE_RECOMMENDATION"


def apply_policy(
    frame: pd.DataFrame, probability: np.ndarray, policy: dict[str, Any]
) -> pd.DataFrame:
    """Attach score, risk band, recommendation and illustrative expected loss."""
    result = frame.copy()
    result["predicted_pd"] = probability
    result["credit_score"] = pd_to_score(probability, policy)
    result["risk_band"] = [risk_band(value) for value in probability]
    result["recommendation"] = [recommendation(value, policy) for value in probability]
    result["lgd_assumption"] = float(policy["lgd_assumption"])
    result["ead_assumption"] = result["requested_amount"]
    result["expected_loss"] = (
        result["predicted_pd"] * result["lgd_assumption"] * result["ead_assumption"]
    )
    result["human_review_required"] = result["recommendation"].isin(
        policy["mandatory_human_review"]
    )
    return result
