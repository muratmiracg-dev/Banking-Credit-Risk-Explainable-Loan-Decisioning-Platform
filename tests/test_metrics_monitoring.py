from __future__ import annotations

import unittest

import numpy as np
import pandas as pd

from credit_risk.metrics import build_decile_table, evaluate_binary
from credit_risk.monitoring import population_stability_index


class MetricsMonitoringTests(unittest.TestCase):
    def test_binary_metrics_for_separable_model(self) -> None:
        truth = np.array([0, 0, 0, 1, 1, 1])
        probability = np.array([0.02, 0.08, 0.20, 0.65, 0.80, 0.95])
        metrics = evaluate_binary(truth, probability, adverse_threshold=0.5)
        self.assertAlmostEqual(metrics["roc_auc"], 1.0)
        self.assertAlmostEqual(metrics["sensitivity"], 1.0)
        self.assertAlmostEqual(metrics["specificity"], 1.0)

    def test_deciles_capture_all_rows(self) -> None:
        rows = 100
        deciles = build_decile_table(
            pd.Series([f"A-{idx}" for idx in range(rows)]),
            pd.Series(([0] * 70) + ([1] * 30)),
            np.linspace(0.01, 0.80, rows),
        )
        self.assertEqual(len(deciles), 10)
        self.assertEqual(int(deciles["applications"].sum()), rows)
        self.assertAlmostEqual(deciles["cumulative_default_capture"].iloc[-1], 1.0)

    def test_psi_is_zero_for_identical_distributions(self) -> None:
        values = np.linspace(0.01, 0.99, 500)
        self.assertAlmostEqual(population_stability_index(values, values), 0.0)

    def test_psi_detects_shift(self) -> None:
        reference = np.linspace(0.01, 0.50, 1000)
        shifted = np.linspace(0.40, 0.99, 1000)
        self.assertGreater(population_stability_index(reference, shifted), 0.25)


if __name__ == "__main__":
    unittest.main()
