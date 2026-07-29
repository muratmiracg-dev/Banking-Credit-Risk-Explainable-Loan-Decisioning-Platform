# Model and platform risk register

| ID | Risk | Inherent severity | Current control | Residual status | Owner |
|---|---|---|---|---|---|
| R-01 | Synthetic data are not representative | Critical | Explicit scope and production prohibition | Open | Model Risk |
| R-02 | Age-band allocation disparity | High | Disaggregated audit and escalation | Open - blocker | Fair Lending / Legal |
| R-03 | Calibration deterioration | High | Monthly Brier, slope and observed-vs-predicted review | Monitored | Model Operations |
| R-04 | Population drift | High | Score and feature PSI | Monitored | Model Operations |
| R-05 | Explanation misread as causality | High | Explainability standard and response notice | Open training need | Model Risk |
| R-06 | Human rubber-stamping | High | Meaningful oversight standard and override audit design | Open process need | Credit Policy |
| R-07 | Threshold change without approval | High | Config separation and review checklist | Open workflow need | Credit Policy |
| R-08 | Unauthorized API access | High | API key option, network policy and secret references | Partial | Security |
| R-09 | Dependency vulnerability | Medium | Dependabot, pip-audit, Trivy and CodeQL | Monitored | Platform Engineering |
| R-10 | Expected loss mistaken for IFRS 9 | High | Repeated illustrative-only disclaimer | Controlled for demo | Finance / Model Risk |
| R-11 | Model artifact tampering | High | Versioned repository and hashes | Partial; signing needed | Platform Engineering |
| R-12 | Incomplete adverse-action notice | Critical | Output explicitly not legally sufficient | Open; downstream design required | Legal / Compliance |

Real use requires an accountable owner, target date, risk acceptance authority and evidence for
every open item.
