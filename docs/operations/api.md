# API guide

## Endpoints

| Method | Path | Purpose |
|---|---|---|
| `GET` | `/healthz` | Process health |
| `GET` | `/readyz` | Model readiness and version |
| `GET` | `/api/v1/model` | Model metadata |
| `GET` | `/api/v1/summary` | Executive synthetic metrics |
| `POST` | `/api/v1/score` | Recommendation-only scoring |
| `GET` | `/metrics` | Prometheus exposition |

## Request controls

- Extra fields are rejected.
- Protected attributes are not part of the schema.
- Numeric values have explicit ranges.
- Categories use fixed literal values.
- API key enforcement activates when `CREDIT_RISK_API_KEY` is set.

## Response controls

The scoring response includes a prominent scope notice. `human_review_required` is always true
for `REFER` and `DECLINE_RECOMMENDATION`.

See [`docs/resources/example_score_request.json`](../resources/example_score_request.json) for a
valid request.
