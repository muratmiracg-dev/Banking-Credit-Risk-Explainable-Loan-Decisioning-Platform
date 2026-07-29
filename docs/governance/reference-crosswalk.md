# Governance reference crosswalk

This is a design crosswalk, not a legal or regulatory compliance statement.

| Reference | Relevant principle | Project evidence | Gap / required work |
|---|---|---|---|
| [Basel credit risk principles (2025)](https://www.bis.org/bcbs/publ/d595.pdf) | Sound credit granting, measurement, monitoring and independent assessment | Temporal validation, policy separation, monthly monitoring, validation report | Board-approved strategy, real portfolio governance and independent review absent |
| [EBA loan origination and monitoring guidelines](https://www.eba.europa.eu/sites/default/files/document_library/Publications/Guidelines/2020/Guidelines%20on%20loan%20origination%20and%20monitoring/884283/EBA%20GL%202020%2006%20Final%20Report%20on%20GL%20on%20loan%20origination%20and%20monitoring.pdf) | Creditworthiness assessment, data, governance and monitoring | Application-time contract, data-quality checks, human review | Jurisdiction, product and institution applicability not assessed |
| [EU AI Act](https://eur-lex.europa.eu/eli/reg/2024/1689/oj) | High-risk context, risk management, data governance, transparency, human oversight and monitoring | Model card, data contract, oversight standard, monitoring runbook | No conformity assessment, QMS, registration or legal determination |
| [NIST AI RMF 1.0](https://www.nist.gov/itl/ai-risk-management-framework) | Govern, Map, Measure, Manage | Governance documents, metrics, fairness review, incident runbook | Voluntary framework; organization-specific profile and accountability not implemented |
| [IFRS 9](https://www.ifrs.org/issued-standards/list-of-standards/ifrs-9-financial-instruments/) | Expected-credit-loss terminology | Transparent PD x LGD x EAD scenario | No staging, lifetime ECL, SICR, discounting, recoveries or macro scenarios |
| [SHAP](https://shap.readthedocs.io/en/latest/) | Additive model explanation | Exact Linear SHAP and additivity gate | Non-causal; legal notice suitability not established |
| [Fairlearn assessment](https://fairlearn.org/main/user_guide/assessment/index.html) | Disaggregated performance and fairness metrics | DP, EO and group performance review | Confidence intervals, intersectionality, causal and legal analysis remain open |

## Crosswalk rule

No project document may use “compliant”, “certified” or “production ready” without separate
qualified evidence and approval.
