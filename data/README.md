# Data

All data in this repository are deterministic and synthetic.

| File | Purpose |
|---|---|
| `data/samples/loan_applications_sample.csv` | 250-row unscored reviewer sample |
| `data/samples/scored_applications_sample.csv` | 250-row scored reviewer sample |
| `artifacts/data/synthetic_loan_applications.csv.gz` | Full 48,000-row generated portfolio |
| `artifacts/data/scored_loan_applications.csv.gz` | Full scored portfolio and policy output |

The generator uses seed `20250729`; the canonical unscored portfolio SHA-256 is
`a47bf52861e50cb2fd83f48dcf53d53361fccaadfbcf2dbb186af5826aa44799`.

`gender` and `age_band` are synthetic audit attributes. They are excluded from training,
scoring and reason-code generation. They must not be treated as production-ready protected
attribute definitions.
