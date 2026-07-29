# Observability

The stack exposes service-health metrics without exporting application inputs or applicant-level
PDs.

- Prometheus scrapes `/metrics`.
- Grafana provisions a four-panel service dashboard.
- Alert rules cover availability, error rate and P95 latency.
- Model-quality monitoring is generated offline in
  `artifacts/monitoring/monthly_monitoring.csv`.

Operational telemetry and model-risk telemetry are separate because their data maturity,
owners and response procedures differ.
