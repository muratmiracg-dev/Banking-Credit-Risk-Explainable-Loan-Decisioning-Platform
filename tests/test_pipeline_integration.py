from __future__ import annotations

import copy
import json
import tempfile
import unittest
from pathlib import Path

import yaml

from credit_risk.config import load_config
from credit_risk.pipeline import manifest_as_json, run_pipeline

ROOT = Path(__file__).resolve().parents[1]


class PipelineIntegrationTests(unittest.TestCase):
    def test_small_end_to_end_pipeline(self) -> None:
        config = copy.deepcopy(load_config(ROOT / "config/project.yaml"))
        config["data"]["rows"] = 4000
        config["model"]["minimum_oot_auc"] = 0.50
        config["model"]["calibration_slope_range"] = [0.10, 3.00]
        with tempfile.TemporaryDirectory() as directory:
            temp_root = Path(directory)
            (temp_root / "config").mkdir()
            config_path = temp_root / "config/project.yaml"
            config_path.write_text(yaml.safe_dump(config), encoding="utf-8")
            manifest = run_pipeline(temp_root, config_path)
            self.assertEqual(manifest["pipeline_status"], "PASS")
            self.assertTrue(
                (temp_root / "artifacts/model/champion_logistic_pipeline.joblib").is_file()
            )
            self.assertTrue((temp_root / "artifacts/metrics/fairness_summary.csv").is_file())
            self.assertTrue((temp_root / "artifacts/monitoring/monthly_monitoring.csv").is_file())
            compact = json.loads(manifest_as_json(manifest))
            self.assertEqual(
                compact["generated_artifact_count"], len(manifest["generated_artifacts"])
            )


if __name__ == "__main__":
    unittest.main()
