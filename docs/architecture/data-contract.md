# Data contract

## Online model fields

The API accepts 17 numeric and 6 categorical application-time predictors. Extra fields are
rejected.

| Domain | Fields |
|---|---|
| Affordability | `monthly_income`, `requested_amount`, `term_months`, `existing_debt`, `monthly_debt_payment`, `debt_to_income` |
| Employment | `employment_type`, `employment_tenure_months` |
| Credit history | `credit_history_months`, `delinquencies_12m`, `delinquencies_36m`, `inquiries_6m`, `open_accounts`, `bureau_score` |
| Liquidity | `savings_balance`, `current_account_balance` |
| Revolving credit | `revolving_utilization` |
| Relationship | `prior_customer_months`, `income_verified`, `channel` |
| Context | `region`, `housing_status`, `purpose` |

## Offline-only fields

| Field | Purpose | Model access |
|---|---|---|
| `application_id` | Traceability | Identifier only |
| `application_date` | Temporal split and monitoring | Not a predictor |
| `default_12m` | Synthetic outcome | Training and evaluation target |
| `gender` | Fairness audit | Prohibited |
| `age_band` | Fairness audit | Prohibited |

## Quality rules

- Application ID is unique and non-null.
- Target is binary.
- Model fields are complete in the generated portfolio.
- Bureau score is within 300-850.
- Utilization and DTI are range-checked in API validation.
- Dates determine development, validation and OOT assignment.
- Production-decision capability remains disabled in configuration.

## Data classification

The committed data are synthetic and contain no real personal information. A production
implementation must define personal-data classification, lawful basis, retention, deletion,
consent or notice, access control and data-subject rights separately.
