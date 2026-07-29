# Case study

## Challenge

A credit model cannot be governed as an isolated notebook. Decision makers need calibrated
probabilities, a transparent policy, reviewer evidence, fairness diagnostics, drift monitoring
and a defensible operating boundary.

## Approach

The project builds a deterministic synthetic portfolio, uses temporal model development,
selects an interpretable champion, maps PD to a recommendation and surrounds the model with
explanation, fairness, monitoring, API, BI and governance controls.

## Result

- OOT ROC AUC: 0.738
- Gini: 0.475
- Calibration slope: 0.981
- Approval recommendation rate: 41.7%
- Maximum monthly score PSI: 0.017
- Linear SHAP additivity error: 2.66e-15

## Responsible finding

The age-band allocation difference is 36.7 percentage points and is treated as a governance
blocker. The case study demonstrates that excluding a protected field does not remove the need
to analyze outcomes and proxy pathways.

## Business value

The repository shows how analytics, model risk, credit policy, compliance, engineering and
operations can evaluate the same decision chain using shared evidence.
