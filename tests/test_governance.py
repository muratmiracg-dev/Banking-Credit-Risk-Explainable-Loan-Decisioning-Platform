from __future__ import annotations

import unittest
from pathlib import Path

import numpy as np
import pandas as pd

from credit_risk.config import load_config
from credit_risk.data import PROTECTED_ATTRIBUTES
from credit_risk.fairness import fairness_audit
from credit_risk.validation import validate_portfolio

ROOT = Path(__file__).resolve().parents[1]


class GovernanceTests(unittest.TestCase):
    def test_protected_attributes_are_excluded_from_model_config(self) -> None:
        config = load_config(ROOT / "config/project.yaml")
        self.assertEqual(config["model"]["protected_attributes_excluded"], PROTECTED_ATTRIBUTES)

    def test_fairness_audit_flags_material_signal(self) -> None:
        frame = pd.DataFrame(
            {
                "gender": ["A"] * 10 + ["B"] * 10,
                "age_band": ["X"] * 10 + ["Y"] * 10,
                "recommendation": ["APPROVE_RECOMMENDATION"] * 9
                + ["REFER"]
                + ["APPROVE_RECOMMENDATION"]
                + ["REFER"] * 9,
                "default_12m": [0, 1] * 10,
                "predicted_pd": [0.1, 0.2] * 10,
            }
        )
        _, summary = fairness_audit(frame, ["gender"])
        self.assertEqual(summary.loc[0, "diagnostic_status"], "GOVERNANCE_REVIEW_REQUIRED")

    def test_fairness_audit_rejects_invalid_governance_inputs(self) -> None:
        valid = pd.DataFrame(
            {
                "gender": ["A", "B"],
                "recommendation": ["REFER", "APPROVE_RECOMMENDATION"],
                "default_12m": [0, 1],
                "predicted_pd": [0.1, 0.8],
            }
        )
        invalid_cases = [
            valid.assign(predicted_pd=[0.1, np.nan]),
            valid.assign(predicted_pd=[0.1, 1.1]),
            valid.assign(default_12m=[0, 2]),
            valid.assign(gender=["A", " "]),
        ]
        for invalid in invalid_cases:
            with (
                self.subTest(columns=invalid.to_dict(orient="list")),
                self.assertRaises(ValueError),
            ):
                fairness_audit(invalid, ["gender"])

        with self.assertRaises(ValueError):
            fairness_audit(valid, [])
        with self.assertRaises(ValueError):
            fairness_audit(valid, ["missing_attribute"])

    def test_generated_portfolio_passes_controls(self) -> None:
        config = load_config(ROOT / "config/project.yaml")
        frame = pd.read_csv(ROOT / "data/samples/loan_applications_sample.csv")
        checks = validate_portfolio(frame, config)
        self.assertTrue(checks["status"].eq("PASS").all())


if __name__ == "__main__":
    unittest.main()
