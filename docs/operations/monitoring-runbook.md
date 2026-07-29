# Model monitoring runbook

## Cadence

| Control | Cadence | Data maturity |
|---|---|---|
| API availability, latency and errors | Continuous | Immediate |
| Input schema and missingness | Daily | Immediate |
| Score and feature PSI | Monthly | Immediate |
| Approval recommendation rate | Monthly | Immediate |
| Observed default rate, AUC and Brier | Monthly after target maturity | 12-month label maturity |
| Fairness review | Quarterly and after material policy/model change | Appropriate outcome maturity |
| Full model validation | At least annually and after trigger | Complete evidence |

## Triage levels

| Signal | Green | Amber | Red |
|---|---|---|---|
| Score PSI | `< 0.10` | `0.10 to < 0.25` | `>= 0.25` |
| AUC drop vs validation | `< 0.03` | `0.03 to < 0.05` | `>= 0.05` |
| Approval-rate change | `< 8 pp` | `>= 8 pp` | Committee-defined escalation |
| Missing model fields | `0%` | Investigate any non-zero | `>= 2%` |

These are internal project triage levels, not regulatory thresholds.

## Amber procedure

1. Confirm data completeness and label maturity.
2. Segment by channel, region, purpose and relevant operational cohorts.
3. Check preprocessing category changes and unknown values.
4. Compare score and top-feature distributions.
5. Review policy or upstream process changes.
6. Record the investigation and owner.

## Red procedure

1. Open a model incident.
2. Restrict or pause affected use under approved authority.
3. Preserve inputs, outputs, model version, policy version and monitoring evidence.
4. Notify Model Risk, Credit Policy, Operations, Compliance and Security as applicable.
5. Evaluate rollback, fallback or manual-only processing.
6. Require documented approval before resumption.

## Fairness trigger

Any material change in disaggregated allocation, error rates or complaints requires specialist
review. A single metric or threshold cannot close the issue.
