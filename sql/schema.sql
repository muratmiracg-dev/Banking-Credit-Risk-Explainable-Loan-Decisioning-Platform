CREATE SCHEMA IF NOT EXISTS credit_risk;
CREATE SCHEMA IF NOT EXISTS credit_risk_governance;

CREATE TABLE IF NOT EXISTS credit_risk.model_registry (
    model_version text PRIMARY KEY,
    model_name text NOT NULL,
    target_name text NOT NULL,
    development_start date NOT NULL,
    development_end date NOT NULL,
    validation_end date NOT NULL,
    approval_status text NOT NULL CHECK (approval_status IN ('DEVELOPMENT', 'VALIDATED', 'APPROVED', 'RETIRED')),
    artifact_sha256 text NOT NULL,
    created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS credit_risk.loan_application (
    application_id text PRIMARY KEY,
    application_date date NOT NULL,
    sample_split text NOT NULL CHECK (sample_split IN ('development', 'validation', 'out_of_time')),
    channel text NOT NULL,
    region text NOT NULL,
    employment_type text NOT NULL,
    monthly_income numeric(16, 2) NOT NULL CHECK (monthly_income > 0),
    requested_amount numeric(16, 2) NOT NULL CHECK (requested_amount > 0),
    term_months integer NOT NULL CHECK (term_months > 0),
    debt_to_income numeric(8, 5) NOT NULL,
    revolving_utilization numeric(8, 5) NOT NULL,
    bureau_score integer NOT NULL CHECK (bureau_score BETWEEN 300 AND 850),
    default_12m smallint NOT NULL CHECK (default_12m IN (0, 1)),
    predicted_pd numeric(10, 8) NOT NULL CHECK (predicted_pd BETWEEN 0 AND 1),
    credit_score integer NOT NULL CHECK (credit_score BETWEEN 300 AND 850),
    risk_band char(1) NOT NULL CHECK (risk_band IN ('A', 'B', 'C', 'D', 'E', 'F')),
    recommendation text NOT NULL CHECK (
        recommendation IN ('APPROVE_RECOMMENDATION', 'REFER', 'DECLINE_RECOMMENDATION')
    ),
    expected_loss numeric(18, 2) NOT NULL,
    human_review_required boolean NOT NULL,
    model_version text NOT NULL REFERENCES credit_risk.model_registry(model_version),
    scored_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS credit_risk.reason_code (
    application_id text NOT NULL REFERENCES credit_risk.loan_application(application_id),
    reason_rank smallint NOT NULL CHECK (reason_rank BETWEEN 1 AND 10),
    reason_code text NOT NULL,
    feature_name text NOT NULL,
    shap_log_odds numeric(18, 10) NOT NULL,
    direction text NOT NULL CHECK (direction IN ('RISK_UP', 'RISK_DOWN')),
    PRIMARY KEY (application_id, reason_rank)
);

CREATE TABLE IF NOT EXISTS credit_risk.model_monitoring_monthly (
    model_version text NOT NULL REFERENCES credit_risk.model_registry(model_version),
    monitoring_month date NOT NULL,
    applications integer NOT NULL,
    observed_default_rate numeric(10, 8) NOT NULL,
    average_predicted_pd numeric(10, 8) NOT NULL,
    roc_auc numeric(10, 8),
    brier numeric(10, 8),
    approval_rate numeric(10, 8) NOT NULL,
    score_psi numeric(10, 8) NOT NULL,
    alert_status text NOT NULL CHECK (alert_status IN ('GREEN', 'AMBER', 'RED')),
    PRIMARY KEY (model_version, monitoring_month)
);

CREATE TABLE IF NOT EXISTS credit_risk_governance.fairness_audit (
    model_version text NOT NULL REFERENCES credit_risk.model_registry(model_version),
    audit_date date NOT NULL,
    protected_attribute text NOT NULL,
    group_name text NOT NULL,
    applications integer NOT NULL,
    approval_rate numeric(10, 8) NOT NULL,
    good_applicant_approval_rate numeric(10, 8) NOT NULL,
    defaulting_applicant_approval_rate numeric(10, 8) NOT NULL,
    roc_auc numeric(10, 8),
    brier numeric(10, 8),
    PRIMARY KEY (model_version, audit_date, protected_attribute, group_name)
);

COMMENT ON SCHEMA credit_risk_governance IS
'Restricted analytical schema. Protected attributes are prohibited from online scoring.';
