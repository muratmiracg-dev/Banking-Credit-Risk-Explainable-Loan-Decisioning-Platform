from __future__ import annotations

import unittest
from pathlib import Path

import pandas as pd

from credit_risk.service import ScoringService

ROOT = Path(__file__).resolve().parents[1]


class ServiceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.service = ScoringService.load(ROOT)
        sample = pd.read_csv(ROOT / "data/samples/loan_applications_sample.csv").iloc[0]
        cls.application = {
            feature: sample[feature] for feature in cls.service.model.feature_names_in_
        }

    def test_score_contract(self) -> None:
        output = self.service.score(self.application, "test-request")
        self.assertEqual(output["request_id"], "test-request")
        self.assertGreaterEqual(output["probability_of_default_12m"], 0)
        self.assertLessEqual(output["probability_of_default_12m"], 1)
        self.assertEqual(len(output["reason_codes"]), 4)
        self.assertIn("Decision support only", output["scope_notice"])

    def test_protected_attributes_are_not_required(self) -> None:
        self.assertNotIn("gender", self.application)
        self.assertNotIn("age_band", self.application)


if __name__ == "__main__":
    unittest.main()
