# Model card

## Model identity

| Field | Value |
|---|---|
| Name | Aurelia Retail Unsecured PD Model |
| Version | 1.0.0 |
| Champion | Logistic regression |
| Target | Synthetic 12-month default |
| Development window | 2022-01-01 to 2024-06-30 |
| Validation window | 2024-07-01 to 2024-12-31 |
| Out-of-time window | 2025-01-01 to 2025-12-31 |
| Intended user | Authorized credit analyst / model reviewer |
| Current status | Portfolio demonstration; not approved for real lending |

## Intended use

- Estimate 12-month PD on schema-valid synthetic unsecured-loan applications.
- Support model validation, risk segmentation, policy scenarios and reviewer education.
- Demonstrate an auditable human-in-the-loop decision-support architecture.

## Prohibited use

- Final approval or decline.
- Pricing, limit assignment or collections treatment.
- Production adverse-action notices.
- Scoring real applicants without redevelopment and approval.
- Claiming regulatory, legal, ethical or accounting compliance.

## Model inputs

Seventeen numeric and six categorical application-time predictors are listed in the
[data contract](../architecture/data-contract.md). `gender` and `age_band` are excluded from
training, scoring and explanations.

## Performance

| Metric | Validation | Out-of-time |
|---|---:|---:|
| ROC AUC | 0.733 | 0.738 |
| Gini | 0.466 | 0.475 |
| PR AUC | 0.403 | 0.421 |
| KS | 0.336 | 0.361 |
| Brier | 0.126 | 0.134 |
| Calibration slope | 0.969 | 0.981 |

## Explainability

For the transformed linear model:

`SHAP_j = coefficient_j × (transformed_value_j - development_mean_j)`

Contributions are in log-odds. The maximum OOT reconstruction error is `2.66e-15`.
Explanations are non-causal and not legally sufficient notices.

## Fairness evidence

| Attribute | DP difference | EO difference | Disposition |
|---|---:|---:|---|
| Gender | 1.6 pp | 1.7 pp | No material signal at the internal 10 pp triage level |
| Age band | 36.7 pp | 37.5 pp | **Governance review required** |

The 10 percentage-point level is an internal project signal, not a legal standard.

## Limitations

- Synthetic data do not establish population representativeness.
- Outcome generation and model specification share a controlled simulated structure.
- No reject inference, affordability policy, fraud or macroeconomic stress scenarios.
- Expected loss is illustrative, not IFRS 9 compliant.
- Fairness findings require causal, legal and stakeholder analysis.
- No independent validation or production approval has occurred.

## Monitoring

Monthly controls cover ROC AUC, Brier, default rate, approval rate, score PSI, bureau-score
PSI and DTI PSI. See the [monitoring runbook](../operations/monitoring-runbook.md).
