# Model validation report

## Executive opinion

The champion passes the predefined synthetic-project discrimination, calibration,
explainability and reproducibility controls. It is suitable for portfolio demonstration and
controlled technical testing. It is **not** validated for real lending because the data are
synthetic, external validity is untested and the age-band allocation gap requires governance
review.

## Validation scope

- Data generation and temporal split
- Feature eligibility and protected-field exclusion
- Champion and challenger comparison
- Discrimination and calibration
- Risk deciles and policy thresholds
- Linear SHAP numerical identity
- Fairness diagnostics
- Monthly monitoring
- Operational and artifact controls

## Findings

| ID | Finding | Severity | Evidence | Disposition |
|---|---|---|---|---|
| VAL-01 | OOT AUC exceeds 0.700 gate | Pass | AUC 0.738 | Accept for synthetic scope |
| VAL-02 | Calibration slope is within gate | Pass | 0.981 | Accept for synthetic scope |
| VAL-03 | SHAP additivity error is negligible | Pass | 2.66e-15 | Accept |
| VAL-04 | Data and safety checks pass | Pass | 6/6 | Accept |
| VAL-05 | Monthly score PSI remains below warning | Pass | max 0.017 | Continue monitoring |
| VAL-06 | Age-band allocation disparity | High | DP 36.7 pp; EO 37.5 pp | Governance review required |
| VAL-07 | Data are synthetic | High | Generator and disclaimer | Prohibit real use |
| VAL-08 | No independent validation | High | Portfolio project status | Required before pilot |

## Challenge observations

1. Logistic regression appropriately remains champion because it leads validation performance
   and supports exact explanations.
2. The OOT period contains a synthetic macro-stress uplift; performance remains stable, but this
   does not substitute for real cycle coverage.
3. Policy thresholds are transparent and scenario-tested; they have not been approved by a
   credit committee.
4. Protected-field exclusion alone does not establish fairness. The age-band finding is material.
5. The expected-loss calculation is fit for a teaching scenario only.

## Validation disposition

`PORTFOLIO_COMPLETE / PRODUCTION_NOT_APPROVED`

Exit criteria for a shadow pilot are listed in the
[production readiness checklist](../operations/production-readiness-checklist.md).
