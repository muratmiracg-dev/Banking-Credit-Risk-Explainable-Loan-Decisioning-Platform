# Explainability standard

## Method

The champion is a logistic regression over standardized numeric variables and one-hot encoded
categorical variables. Under the feature-independence assumption, exact additive Linear SHAP
in log-odds is:

`phi_j = beta_j × (x_j - E[x_j])`

The base value equals the model intercept plus the coefficient-weighted development mean.

## Required controls

- Preserve transformed feature names and development background means.
- Verify `base + sum(phi) = model log-odds` within `1e-10`.
- Rank global drivers by mean absolute SHAP.
- Return only the top four risk-increasing local contributions to the reviewer.
- Keep the full local contribution evidence for audit.
- Never use protected attributes in the model or reason codes.

## Interpretation boundaries

- SHAP explains model behavior, not causality.
- A large contribution does not prove an applicant caused an outcome.
- Correlated features can redistribute attribution.
- A model reason code is not automatically an adverse-action reason.
- Operational wording requires policy, legal and data-quality review.

Reference: [SHAP documentation](https://shap.readthedocs.io/en/latest/).
