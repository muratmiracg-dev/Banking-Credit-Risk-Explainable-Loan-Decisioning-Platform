# Fairness assessment

## Purpose

The assessment checks whether recommendation allocation and predictive behavior differ across
synthetic `gender` and `age_band` groups. It is a diagnostic input to governance, not a legal
or moral definition of fairness.

## Separation control

- Protected attributes do not enter preprocessing, training or scoring.
- The API schema cannot accept them.
- SHAP reason codes cannot include them.
- Group-level evaluation occurs only after scoring in a restricted analytical context.

## Metrics

- Approval recommendation rate
- Good-applicant approval rate (equal-opportunity diagnostic)
- Defaulting-applicant approval rate
- ROC AUC and Brier by group
- Demographic-parity difference
- Equal-opportunity difference

## Result

| Attribute | Minimum group size | DP difference | EO difference | AUC range | Status |
|---|---:|---:|---:|---:|---|
| Gender | 5,991 | 1.6 pp | 1.7 pp | 1.6 pp | No material signal at 10 pp triage level |
| Age band | 900 | 36.7 pp | 37.5 pp | 2.5 pp | **Governance review required** |

The 10 percentage-point triage level is an internal project convention only. Fairlearn warns
that fairness metrics can be used incautiously; the project therefore reports several
disaggregated metrics and avoids a blanket “fair” label.

## Required investigation

1. Inspect the distribution of credit history, employment tenure, income, DTI and bureau score
   across age bands.
2. Test legitimate-feature pathways and proxy effects.
3. Quantify uncertainty with confidence intervals and intersectional groups.
4. Re-evaluate policy thresholds and reviewer procedures.
5. Perform jurisdiction-specific legal and consumer-impact analysis.
6. Document stakeholder input, mitigation decisions and residual risk.

## Current disposition

No production use. The finding is a blocker, not a dashboard footnote.

Reference: [Fairlearn assessment documentation](https://fairlearn.org/main/user_guide/assessment/index.html).
