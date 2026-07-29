# Threat model

## Protected assets

- Model and policy versions
- Application inputs and decision evidence
- Reviewer identity and rationale
- API secrets and service availability
- Monitoring and incident records

## Trust boundaries

1. Client to API
2. API to model artifact
3. Approved data ingestion to PostgreSQL
4. General reporting schema to restricted governance schema
5. CI/CD to deployment environment

## Threats and controls

| Threat | Example | Reference control | Production enhancement |
|---|---|---|---|
| Spoofing | Unauthorized scoring request | API key option | OAuth2/mTLS, workload identity |
| Tampering | Replaced model artifact | Repository hash and model metadata | Signed artifacts, attestations, immutable registry |
| Repudiation | Reviewer denies override | Request ID and audit design | Append-only signed decision log |
| Information disclosure | Protected-group data exposed | Separate governance schema | Column encryption, ABAC, DLP and audited access |
| Denial of service | Scoring API exhausted | Resource limits and alerts | Rate limits, autoscaling and WAF |
| Elevation of privilege | Container escape | Non-root, read-only, no capabilities | Policy enforcement, image signing and runtime security |
| Model abuse | Out-of-domain inputs | Pydantic ranges and category contract | OOD detection and risk-based throttling |
| Supply chain | Malicious dependency | Dependabot, CodeQL, pip-audit, Trivy | Lock files, SBOM, provenance and signed releases |

## Out of scope

The repository is not a full production security architecture. It contains no identity
provider, customer data, managed key service or core-banking connector.
