"""Portfolio and artifact validation controls."""

from __future__ import annotations

from typing import Any

import pandas as pd

from credit_risk.data import CATEGORICAL_FEATURES, NUMERIC_FEATURES, PROTECTED_ATTRIBUTES, TARGET


def validate_portfolio(frame: pd.DataFrame, config: dict[str, Any]) -> pd.DataFrame:
    """Return auditable data-quality checks; raise if any critical check fails."""
    expected = {
        "application_id",
        "application_date",
        *NUMERIC_FEATURES,
        *CATEGORICAL_FEATURES,
        *PROTECTED_ATTRIBUTES,
        TARGET,
    }
    checks = [
        {
            "check_id": "DQ-001",
            "control": "Expected schema present",
            "actual": len(expected.intersection(frame.columns)),
            "expected": len(expected),
            "status": "PASS" if expected.issubset(frame.columns) else "FAIL",
        },
        {
            "check_id": "DQ-002",
            "control": "Application ID unique",
            "actual": int(frame["application_id"].nunique()),
            "expected": len(frame),
            "status": "PASS" if frame["application_id"].is_unique else "FAIL",
        },
        {
            "check_id": "DQ-003",
            "control": "Target binary",
            "actual": ",".join(map(str, sorted(frame[TARGET].unique()))),
            "expected": "0,1",
            "status": "PASS" if set(frame[TARGET].unique()) == {0, 1} else "FAIL",
        },
        {
            "check_id": "DQ-004",
            "control": "Model feature completeness",
            "actual": int(frame[NUMERIC_FEATURES + CATEGORICAL_FEATURES].isna().sum().sum()),
            "expected": 0,
            "status": (
                "PASS"
                if frame[NUMERIC_FEATURES + CATEGORICAL_FEATURES].isna().sum().sum() == 0
                else "FAIL"
            ),
        },
        {
            "check_id": "DQ-005",
            "control": "Synthetic-only safety flag",
            "actual": config["project"]["synthetic_only"],
            "expected": True,
            "status": "PASS" if config["project"]["synthetic_only"] else "FAIL",
        },
        {
            "check_id": "DQ-006",
            "control": "Production decisions disabled",
            "actual": config["project"]["production_decisions_permitted"],
            "expected": False,
            "status": (
                "PASS" if not config["project"]["production_decisions_permitted"] else "FAIL"
            ),
        },
    ]
    result = pd.DataFrame(checks)
    if result["status"].eq("FAIL").any():
        raise ValueError("Critical data-quality or safety control failed.")
    return result
