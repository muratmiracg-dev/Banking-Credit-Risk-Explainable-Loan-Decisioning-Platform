# Decision policy

## Policy matrix

| PD | Risk bands | Recommendation | Required action |
|---|---|---|---|
| `< 10%` | A-C | `APPROVE_RECOMMENDATION` | Policy-dependent human confirmation |
| `10% to < 22%` | D-E | `REFER` | Mandatory authorized review |
| `>= 22%` | F | `DECLINE_RECOMMENDATION` | Mandatory review and disclosure workflow |

## Score convention

- Score anchor: 650
- Anchor PD: 10%
- Points to double odds: 50
- Output range: 300-850

## Expected-loss convention

`Illustrative expected loss = PD × 45% LGD × requested amount`

This is a scenario bridge, not IFRS 9 impairment measurement. It excludes staging, significant
increase in credit risk, lifetime PD, discounting, recovery timing and forward-looking
macroeconomic scenarios.

## Ownership

| Decision object | Accountable owner |
|---|---|
| Model estimation | Retail Credit Analytics |
| Model validation | Independent Model Risk |
| Thresholds | Credit Policy Committee |
| Final applicant decision | Authorized credit officer / approved process |
| Disclosure language | Legal and Compliance |
| Production operation | Platform and Model Operations |

Threshold changes require impact analysis, fairness review, validation sign-off and recorded
approval before release.
