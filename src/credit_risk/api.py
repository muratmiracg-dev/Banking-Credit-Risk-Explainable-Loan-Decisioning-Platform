"""FastAPI transport for the recommendation-only scoring service."""

from __future__ import annotations

import json
import os
import time
from pathlib import Path
from typing import Annotated

from fastapi import FastAPI, Header, HTTPException, Response
from prometheus_client import CONTENT_TYPE_LATEST, Counter, Histogram, generate_latest

from credit_risk.schemas import LoanApplication, ScoreResponse
from credit_risk.service import ScoringService

ROOT = Path(os.getenv("CREDIT_RISK_ROOT", Path(__file__).resolve().parents[2]))
EXPECTED_API_KEY = os.getenv("CREDIT_RISK_API_KEY", "")
service = ScoringService.load(ROOT)

REQUESTS = Counter(
    "credit_risk_score_requests_total",
    "Scoring requests by outcome",
    ["outcome"],
)
LATENCY = Histogram(
    "credit_risk_score_latency_seconds",
    "Scoring request latency",
)

app = FastAPI(
    title="Banking Credit Risk Decision-Support API",
    version="1.0.0",
    description=(
        "Synthetic demonstration. Returns a governed recommendation and explanation; "
        "it never executes a final lending decision."
    ),
    docs_url="/docs",
    redoc_url="/redoc",
)


def _authorize(api_key: str | None) -> None:
    if EXPECTED_API_KEY and api_key != EXPECTED_API_KEY:
        REQUESTS.labels(outcome="unauthorized").inc()
        raise HTTPException(status_code=401, detail="Invalid API key")


@app.get("/healthz")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/readyz")
def readiness() -> dict[str, str]:
    return {
        "status": "ready",
        "model": "logistic_regression",
        "version": service.config["project"]["version"],
    }


@app.get("/api/v1/model")
def model_metadata(
    x_api_key: Annotated[str | None, Header()] = None,
) -> dict[str, object]:
    _authorize(x_api_key)
    path = ROOT / "artifacts/model/model_metadata.json"
    return json.loads(path.read_text(encoding="utf-8"))


@app.get("/api/v1/summary")
def executive_summary(
    x_api_key: Annotated[str | None, Header()] = None,
) -> dict[str, object]:
    _authorize(x_api_key)
    path = ROOT / "artifacts/metrics/executive_summary.json"
    return json.loads(path.read_text(encoding="utf-8"))


@app.post("/api/v1/score", response_model=ScoreResponse)
def score(
    application: LoanApplication,
    x_request_id: Annotated[str | None, Header()] = None,
    x_api_key: Annotated[str | None, Header()] = None,
) -> dict[str, object]:
    _authorize(x_api_key)
    started = time.perf_counter()
    try:
        output = service.score(application.model_dump(), x_request_id)
        REQUESTS.labels(outcome="success").inc()
        return output
    except Exception as exc:
        REQUESTS.labels(outcome="error").inc()
        raise HTTPException(status_code=422, detail="Scoring failed validation") from exc
    finally:
        LATENCY.observe(time.perf_counter() - started)


@app.get("/metrics", include_in_schema=False)
def metrics() -> Response:
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)
