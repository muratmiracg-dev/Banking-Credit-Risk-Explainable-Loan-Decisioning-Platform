# ADR-001: Select logistic regression as the governed champion

- Status: Accepted for the synthetic portfolio
- Date: 2026-07-29
- Owners: Retail Credit Analytics and Model Risk

## Context

The project compares logistic regression, histogram gradient boosting and random forest on a
future validation window. The platform needs calibrated PDs, stable auditability and local
reason codes.

## Decision

Use the logistic-regression pipeline as champion. It achieves the best validation ROC AUC
(`0.733`) and Brier score (`0.126`) among the three candidates and supports exact additive
Linear SHAP in transformed log-odds space.

## Consequences

- Probability behavior and coefficients remain directly inspectable.
- SHAP additivity can be checked as a numerical identity.
- Challenger evidence remains available for future redevelopment.
- Interpretability does not eliminate the need for fairness, calibration, validation or
  external-validity review.
