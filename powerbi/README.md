# Power BI project

Open `CreditRiskDashboard.pbip` in Power BI Desktop with Power BI Project support enabled.
The semantic model uses PostgreSQL parameters `PostgreSQLServer` and `PostgreSQLDatabase`;
protected-attribute reporting is isolated in the restricted governance schema.

## Recommended report pages

1. Executive Control Tower — applications, PD, approval recommendation, EL and review rate.
2. Portfolio Risk — exposure and observed default by A-F risk band.
3. Model Performance — ROC AUC, Gini, KS, Brier and calibration.
4. Explainability — global Linear SHAP drivers and filtered reason codes.
5. Policy Simulator — approve/refer thresholds, volume, risk and expected loss.
6. Fairness Review — disaggregated performance and allocation metrics with governance notice.
7. Model Monitoring — monthly ROC AUC, PSI, default rate, approval rate and alerts.
8. Data Quality & Lineage — critical controls, model version and refresh metadata.

The committed `artifacts/plots/executive_dashboard.png` is the visual design reference. This
starter intentionally contains no production credentials, no row-level protected attributes in
the general model, and no claim of regulatory compliance.
