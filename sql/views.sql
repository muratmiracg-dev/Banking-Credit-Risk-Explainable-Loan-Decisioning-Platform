CREATE OR REPLACE VIEW credit_risk.vw_executive_kpis AS
SELECT
    model_version,
    COUNT(*) AS applications,
    AVG(default_12m::numeric) AS observed_default_rate,
    AVG(predicted_pd) AS average_predicted_pd,
    AVG((recommendation = 'APPROVE_RECOMMENDATION')::int::numeric) AS approval_rate,
    SUM(requested_amount) AS requested_exposure,
    SUM(expected_loss) AS expected_loss,
    AVG(human_review_required::int::numeric) AS human_review_rate
FROM credit_risk.loan_application
GROUP BY model_version;

CREATE OR REPLACE VIEW credit_risk.vw_risk_band_performance AS
SELECT
    model_version,
    risk_band,
    COUNT(*) AS applications,
    SUM(requested_amount) AS exposure,
    AVG(predicted_pd) AS average_predicted_pd,
    AVG(default_12m::numeric) AS observed_default_rate,
    SUM(expected_loss) AS expected_loss
FROM credit_risk.loan_application
GROUP BY model_version, risk_band;

CREATE OR REPLACE VIEW credit_risk.vw_recommendation_performance AS
SELECT
    model_version,
    recommendation,
    COUNT(*) AS applications,
    SUM(requested_amount) AS exposure,
    AVG(predicted_pd) AS average_predicted_pd,
    AVG(default_12m::numeric) AS observed_default_rate,
    SUM(expected_loss) AS expected_loss
FROM credit_risk.loan_application
GROUP BY model_version, recommendation;

CREATE OR REPLACE VIEW credit_risk_governance.vw_fairness_disparity AS
SELECT
    model_version,
    audit_date,
    protected_attribute,
    MAX(approval_rate) - MIN(approval_rate) AS demographic_parity_difference,
    MAX(good_applicant_approval_rate) - MIN(good_applicant_approval_rate)
        AS equal_opportunity_difference,
    MAX(defaulting_applicant_approval_rate) - MIN(defaulting_applicant_approval_rate)
        AS defaulting_approval_rate_difference
FROM credit_risk_governance.fairness_audit
GROUP BY model_version, audit_date, protected_attribute;
