#!/usr/bin/env python3
"""Fail fast when the professional delivery package is incomplete."""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
EXPECTED = [
    "artifacts/data/synthetic_loan_applications.csv.gz",
    "artifacts/data/scored_loan_applications.csv.gz",
    "artifacts/model/champion_logistic_pipeline.joblib",
    "artifacts/model/model_metadata.json",
    "artifacts/metrics/executive_summary.json",
    "artifacts/metrics/model_comparison.csv",
    "artifacts/metrics/risk_deciles.csv",
    "artifacts/metrics/fairness_summary.csv",
    "artifacts/monitoring/monthly_monitoring.csv",
    "artifacts/explanations/global_linear_shap_importance.csv",
    "artifacts/plots/executive_dashboard.png",
    "reports/workbook/credit_risk_decision_workbench.xlsx",
    "reports/presentation/credit_risk_executive_deck.pptx",
    "reports/pdf/credit_risk_model_governance_report.pdf",
]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> int:
    missing = [path for path in EXPECTED if not (ROOT / path).is_file()]
    if missing:
        print("Missing required artifacts:", *missing, sep="\n- ")
        return 1
    executive = json.loads(
        (ROOT / "artifacts/metrics/executive_summary.json").read_text(encoding="utf-8")
    )
    fairness = pd.read_csv(ROOT / "artifacts/metrics/fairness_summary.csv")
    monitoring = pd.read_csv(ROOT / "artifacts/monitoring/monthly_monitoring.csv")
    gates = {
        "oot_auc_at_least_0_70": executive["oot_roc_auc"] >= 0.70,
        "calibration_slope_0_75_to_1_25": 0.75 <= executive["oot_calibration_slope"] <= 1.25,
        "shap_additivity_below_1e_10": executive["linear_shap_max_additivity_error"] < 1e-10,
        "monitoring_has_12_months": len(monitoring) == 12,
        "fairness_diagnostic_present": len(fairness) >= 2,
        "synthetic_data_hash_matches_manifest": executive["data_sha256"]
        == json.loads((ROOT / "artifacts/manifest.json").read_text())["executive_summary"][
            "data_sha256"
        ],
    }
    for name, passed in gates.items():
        print(f"{name}: {'PASS' if passed else 'FAIL'}")
    if not all(gates.values()):
        return 1
    for artifact in EXPECTED:
        print(f"{sha256(ROOT / artifact)[:12]}  {artifact}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
