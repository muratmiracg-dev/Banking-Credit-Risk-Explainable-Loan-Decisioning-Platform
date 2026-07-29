from __future__ import annotations

import unittest
from pathlib import Path

import numpy as np
import pandas as pd

from credit_risk.config import load_config
from credit_risk.policy import apply_policy, pd_to_score, recommendation, risk_band

ROOT = Path(__file__).resolve().parents[1]


class PolicyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.policy = load_config(ROOT / "config/project.yaml")["policy"]

    def test_pd_to_score_is_monotonic(self) -> None:
        score = pd_to_score(np.array([0.02, 0.10, 0.30]), self.policy)
        self.assertGreater(score[0], score[1])
        self.assertGreater(score[1], score[2])
        self.assertEqual(score[1], self.policy["score_anchor"])

    def test_recommendation_thresholds(self) -> None:
        self.assertEqual(recommendation(0.05, self.policy), "APPROVE_RECOMMENDATION")
        self.assertEqual(recommendation(0.15, self.policy), "REFER")
        self.assertEqual(recommendation(0.30, self.policy), "DECLINE_RECOMMENDATION")

    def test_risk_bands(self) -> None:
        self.assertEqual(
            [risk_band(value) for value in [0.02, 0.04, 0.08, 0.12, 0.18, 0.30]], list("ABCDEF")
        )

    def test_expected_loss_formula(self) -> None:
        frame = pd.DataFrame({"requested_amount": [100_000.0, 50_000.0]})
        result = apply_policy(frame, np.array([0.10, 0.30]), self.policy)
        self.assertAlmostEqual(result.loc[0, "expected_loss"], 4_500.0)
        self.assertTrue(result.loc[1, "human_review_required"])


if __name__ == "__main__":
    unittest.main()
