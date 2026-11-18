from __future__ import annotations

import unittest
from pathlib import Path

import numpy as np
import pandas as pd

from credit_risk.config import load_config
from credit_risk.monitoring import calibration_in_the_large, monitoring_report

ROOT = Path(__file__).resolve().parents[1]


def _frame(month_defaults: dict[str, tuple[int, float]], size: int = 1000) -> pd.DataFrame:
    """Development, validation and OOT rows; OOT months get the given defaults and PD."""
    rng = np.random.default_rng(7)
    rows = []
    for split, month in (("development", "2024-01"), ("validation", "2024-07")):
        pd_values = np.full(size, 0.15)
        defaults = rng.random(size) < pd_values
        rows.append((split, month, defaults, pd_values))
    for month, (defaults_count, predicted) in month_defaults.items():
        defaults = np.zeros(size, dtype=bool)
        defaults[:defaults_count] = True
        rows.append(("oot", month, defaults, np.full(size, predicted)))
    frames = []
    for split, month, defaults, pd_values in rows:
        frames.append(
            pd.DataFrame(
                {
                    "split": split,
                    "application_date": pd.to_datetime(f"{month}-15"),
                    "default_12m": defaults.astype(int),
                    "predicted_pd": pd_values + np.linspace(-0.01, 0.01, size),
                    "recommendation": "REFER",
                    "bureau_score": np.linspace(600, 760, size),
                    "debt_to_income": np.linspace(0.1, 0.5, size),
                }
            )
        )
    return pd.concat(frames, ignore_index=True)


class CalibrationMonitoringTests(unittest.TestCase):
    def test_actual_to_expected_and_binomial_z(self) -> None:
        result = calibration_in_the_large(np.array([1, 0, 0, 1]), np.array([0.5, 0.5, 0.5, 0.5]))
        self.assertEqual(result["expected_defaults"], 2.0)
        self.assertEqual(result["ae_ratio"], 1.0)
        self.assertEqual(result["z_score"], 0.0)
        with self.assertRaises(ValueError):
            calibration_in_the_large(np.array([]), np.array([]))

    def test_under_prediction_escalates_even_when_ranking_is_stable(self) -> None:
        # 1,000 applications at a 15% predicted PD: 150 expected defaults.
        frame = _frame({"2025-01": (150, 0.15), "2025-02": (175, 0.15), "2025-03": (200, 0.15)})
        report = monitoring_report(
            frame,
            frame["split"].eq("development"),
            frame["split"].eq("validation"),
            load_config(ROOT / "config/project.yaml"),
        ).set_index("monitoring_month")
        self.assertAlmostEqual(report.loc["2025-03", "actual_to_expected_defaults"], 200 / 150)
        self.assertEqual(report.loc["2025-01", "calibration_status"], "GREEN")
        self.assertEqual(report.loc["2025-02", "calibration_status"], "AMBER")
        self.assertEqual(report.loc["2025-03", "calibration_status"], "RED")
        self.assertEqual(report.loc["2025-03", "alert_status"], "RED")

    def test_small_cohort_deviation_is_not_escalated_without_significance(self) -> None:
        frame = _frame({"2025-01": (13, 0.10)}, size=100)
        report = monitoring_report(
            frame,
            frame["split"].eq("development"),
            frame["split"].eq("validation"),
            load_config(ROOT / "config/project.yaml"),
        )
        self.assertAlmostEqual(report.loc[0, "actual_to_expected_defaults"], 1.3)
        self.assertLess(abs(report.loc[0, "calibration_z_score"]), 1.96)
        self.assertEqual(report.loc[0, "calibration_status"], "GREEN")

    def test_month_without_both_outcomes_reports_unknown_auc_drop(self) -> None:
        frame = _frame({"2025-01": (0, 0.02)})
        report = monitoring_report(
            frame,
            frame["split"].eq("development"),
            frame["split"].eq("validation"),
            load_config(ROOT / "config/project.yaml"),
        )
        self.assertTrue(np.isnan(report.loc[0, "roc_auc"]))
        self.assertTrue(np.isnan(report.loc[0, "auc_drop_vs_validation"]))


if __name__ == "__main__":
    unittest.main()
