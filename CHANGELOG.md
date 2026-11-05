# Changelog

## Unreleased

### Fixed

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
