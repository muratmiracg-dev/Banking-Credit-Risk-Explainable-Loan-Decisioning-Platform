"""Champion release gates must stop a model that fails validation thresholds."""

from __future__ import annotations

import copy
import unittest
from pathlib import Path

from credit_risk.config import load_config
from credit_risk.data import assign_split, generate_portfolio
from credit_risk.modeling import train_and_compare

ROOT = Path(__file__).resolve().parents[1]


class ChampionGateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        config = copy.deepcopy(load_config(ROOT / "config/project.yaml"))
        config["data"]["rows"] = 4000
        cls.base_config = config
        cls.frame = generate_portfolio(config)
        cls.split = assign_split(cls.frame, config)

    def config_with(self, **model_overrides: object) -> dict:
        config = copy.deepcopy(self.base_config)
        config["model"].update(model_overrides)
        return config

    def test_champion_passes_attainable_gates(self) -> None:
        config = self.config_with(minimum_oot_auc=0.50, calibration_slope_range=[0.10, 3.00])
        bundle = train_and_compare(self.frame, self.split, config)
        champion = config["model"]["champion"]
        status = bundle.comparison.set_index("model")["deployment_status"]
        self.assertEqual(status[champion], "CHAMPION")
        self.assertEqual((status == "CHAMPION").sum(), 1)

    def test_minimum_auc_gate_blocks_release(self) -> None:
        config = self.config_with(minimum_oot_auc=0.999, calibration_slope_range=[0.10, 3.00])
        with self.assertRaisesRegex(RuntimeError, "minimum validation AUC gate"):
            train_and_compare(self.frame, self.split, config)

    def test_calibration_slope_gate_blocks_release(self) -> None:
        config = self.config_with(minimum_oot_auc=0.50, calibration_slope_range=[5.0, 6.0])
        with self.assertRaisesRegex(RuntimeError, "calibration slope gate"):
            train_and_compare(self.frame, self.split, config)


if __name__ == "__main__":
    unittest.main()
