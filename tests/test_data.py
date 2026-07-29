from __future__ import annotations

import copy
import unittest
from pathlib import Path

from credit_risk.config import load_config
from credit_risk.data import (
    CATEGORICAL_FEATURES,
    NUMERIC_FEATURES,
    PROTECTED_ATTRIBUTES,
    assign_split,
    frame_sha256,
    generate_portfolio,
)

ROOT = Path(__file__).resolve().parents[1]


class DataTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.config = load_config(ROOT / "config/project.yaml")
        cls.small = copy.deepcopy(cls.config)
        cls.small["data"]["rows"] = 1200

    def test_generation_is_deterministic(self) -> None:
        first = generate_portfolio(self.small)
        second = generate_portfolio(self.small)
        self.assertEqual(frame_sha256(first), frame_sha256(second))

    def test_schema_and_ranges(self) -> None:
        frame = generate_portfolio(self.small)
        expected = set(NUMERIC_FEATURES + CATEGORICAL_FEATURES + PROTECTED_ATTRIBUTES)
        self.assertTrue(expected.issubset(frame.columns))
        self.assertTrue(frame["bureau_score"].between(300, 850).all())
        self.assertTrue(frame["revolving_utilization"].between(0, 1).all())
        self.assertEqual(set(frame["default_12m"].unique()), {0, 1})

    def test_temporal_split_has_three_windows(self) -> None:
        frame = generate_portfolio(self.small)
        split = assign_split(frame, self.small)
        self.assertEqual(set(split.unique()), {"development", "validation", "out_of_time"})
        self.assertEqual(len(split), len(frame))


if __name__ == "__main__":
    unittest.main()
