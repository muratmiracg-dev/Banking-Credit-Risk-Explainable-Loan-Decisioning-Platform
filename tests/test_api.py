from __future__ import annotations

import json
import unittest
from pathlib import Path

import pandas as pd
from fastapi.testclient import TestClient

from credit_risk.api import app, service

ROOT = Path(__file__).resolve().parents[1]


class ApiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.client = TestClient(app)

    def test_health_and_readiness(self) -> None:
        self.assertEqual(self.client.get("/healthz").status_code, 200)
        readiness = self.client.get("/readyz")
        self.assertEqual(readiness.status_code, 200)
        self.assertEqual(readiness.json()["status"], "ready")

    def test_model_and_summary(self) -> None:
        self.assertEqual(self.client.get("/api/v1/model").status_code, 200)
        summary = self.client.get("/api/v1/summary")
        self.assertEqual(summary.status_code, 200)
        self.assertEqual(summary.json()["synthetic_applications"], 48000)

    def test_score_endpoint(self) -> None:
        sample = pd.read_csv(ROOT / "data/samples/loan_applications_sample.csv").iloc[0]
        payload = {
            feature: (
                int(sample[feature])
                if feature
                in {
                    "term_months",
                    "employment_tenure_months",
                    "credit_history_months",
                    "delinquencies_12m",
                    "delinquencies_36m",
                    "inquiries_6m",
                    "open_accounts",
                    "bureau_score",
                    "prior_customer_months",
                }
                else float(sample[feature])
                if feature
                in {
                    "monthly_income",
                    "requested_amount",
                    "existing_debt",
                    "monthly_debt_payment",
                    "debt_to_income",
                    "revolving_utilization",
                    "savings_balance",
                    "current_account_balance",
                }
                else sample[feature]
            )
            for feature in service.model.feature_names_in_
        }
        response = self.client.post(
            "/api/v1/score",
            json=payload,
            headers={"X-Request-ID": "integration-test"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["request_id"], "integration-test")
        self.assertEqual(len(response.json()["reason_codes"]), 4)

    def test_documented_example_request_is_accepted(self) -> None:
        payload = json.loads((ROOT / "docs/resources/example_score_request.json").read_text())
        self.assertEqual(self.client.post("/api/v1/score", json=payload).status_code, 200)

    def test_rejects_debt_to_income_inconsistent_with_affordability_fields(self) -> None:
        payload = json.loads((ROOT / "docs/resources/example_score_request.json").read_text())
        # Payments imply (30000 + 85000 / 24) / 52000 = 0.645, but the caller claims 0.05.
        payload["monthly_debt_payment"] = 30_000
        payload["debt_to_income"] = 0.05
        response = self.client.post("/api/v1/score", json=payload)
        self.assertEqual(response.status_code, 422)
        self.assertIn("debt_to_income", response.text)

        payload["debt_to_income"] = round((30_000 + 85_000 / 24) / 52_000, 4)
        self.assertEqual(self.client.post("/api/v1/score", json=payload).status_code, 200)

    def test_rejects_more_recent_than_cumulative_delinquencies(self) -> None:
        payload = json.loads((ROOT / "docs/resources/example_score_request.json").read_text())
        payload["delinquencies_12m"] = 3
        payload["delinquencies_36m"] = 1
        self.assertEqual(self.client.post("/api/v1/score", json=payload).status_code, 422)

    def test_rejects_protected_attribute(self) -> None:
        payload = {"gender": "Female"}
        self.assertEqual(self.client.post("/api/v1/score", json=payload).status_code, 422)

    def test_metrics(self) -> None:
        response = self.client.get("/metrics")
        self.assertEqual(response.status_code, 200)
        self.assertIn("credit_risk_score_requests_total", response.text)


if __name__ == "__main__":
    unittest.main()
