from __future__ import annotations

import copy
import unittest
from pathlib import Path

import yaml

from credit_risk.config import load_config

ROOT = Path(__file__).resolve().parents[1]


class ConfigTests(unittest.TestCase):
    def test_loads_safe_configuration(self) -> None:
        config = load_config(ROOT / "config/project.yaml")
        self.assertTrue(config["project"]["synthetic_only"])
        self.assertFalse(config["project"]["production_decisions_permitted"])

    def test_rejects_production_decisions(self) -> None:
        config = load_config(ROOT / "config/project.yaml")
        unsafe = copy.deepcopy(config)
        unsafe["project"]["production_decisions_permitted"] = True
        path = ROOT / "tmp-unsafe-config.yaml"
        try:
            path.write_text(yaml.safe_dump(unsafe), encoding="utf-8")
            with self.assertRaises(ValueError):
                load_config(path)
        finally:
            path.unlink(missing_ok=True)

    def test_rejects_inverted_thresholds(self) -> None:
        config = load_config(ROOT / "config/project.yaml")
        unsafe = copy.deepcopy(config)
        unsafe["policy"]["approve_max_pd"] = 0.30
        path = ROOT / "tmp-threshold-config.yaml"
        try:
            path.write_text(yaml.safe_dump(unsafe), encoding="utf-8")
            with self.assertRaises(ValueError):
                load_config(path)
        finally:
            path.unlink(missing_ok=True)


if __name__ == "__main__":
    unittest.main()
