from __future__ import annotations

import unittest
from pathlib import Path

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

    def test_generated_portfolio_passes_controls(self) -> None:
        config = load_config(ROOT / "config/project.yaml")
        frame = pd.read_csv(ROOT / "data/samples/loan_applications_sample.csv")
        checks = validate_portfolio(frame, config)
        self.assertTrue(checks["status"].eq("PASS").all())


if __name__ == "__main__":
    unittest.main()
