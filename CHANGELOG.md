# Changelog

## Unreleased

### Fixed

- Monitoring had no calibration check, so every OOT month was GREEN although the model
  under-predicts defaults in 10 of 12 months (observed 18.8% vs predicted 15.9%,
  actual-to-expected 1.19; up to 1.39 in March 2025), understating expected loss. Monthly
  monitoring now reports expected and observed defaults, the A/E ratio and a binomial z-score,
  and escalates when `|A/E - 1|` reaches 0.10 (AMBER) or 0.20 (RED) with `|z| >= 1.96`. Result:
  4 RED, 6 AMBER, 2 GREEN months. The executive summary adds the OOT mean PD, A/E and the
  month counts by status; the validation report records finding VAL-09.
- A month without both outcomes reported an AUC drop of 0.0 (`max(0.0, nan)`) and a GREEN AUC
  status. The drop is now missing and does not count as "no drop".
- Pinned runtime and development dependencies exactly. The committed model is pickled with
  scikit-learn 1.8.0; unpinned installs (including the Docker image) pulled scikit-learn 1.9,
  which loads the pickle across versions and changes the challenger metrics.
- CI now compares the regenerated CSV/JSON evidence with the committed artifacts
  (`scripts/compare_artifacts.py`) instead of only checking that two reruns agree.

## 1.0.0 - 2026-07-29

### Added

- Deterministic 48,000-application synthetic lending portfolio
- Temporal champion/challenger model development
- Credit score, A-F risk bands and transparent recommendation policy
- Exact additive Linear SHAP explanations and reason codes
- Protected-group fairness and performance diagnostics
- Monthly model monitoring and alert triage
- Recommendation-only FastAPI service
- PostgreSQL, Power BI, Excel, PDF and presentation deliverables
- Docker, Kubernetes, Prometheus and Grafana references
- CI, CodeQL, dependency audit, Trivy and Dependabot
- Complete architecture, validation, governance and operational documentation
