"""Deterministic synthetic loan application generator."""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

NUMERIC_FEATURES = [
    "monthly_income",
    "requested_amount",
    "term_months",
    "employment_tenure_months",
    "existing_debt",
    "monthly_debt_payment",
    "debt_to_income",
    "credit_history_months",
    "delinquencies_12m",
    "delinquencies_36m",
    "revolving_utilization",
    "inquiries_6m",
    "open_accounts",
    "bureau_score",
    "savings_balance",
    "current_account_balance",
    "prior_customer_months",
]

CATEGORICAL_FEATURES = [
    "channel",
    "region",
    "employment_type",
    "housing_status",
    "purpose",
    "income_verified",
]

PROTECTED_ATTRIBUTES = ["gender", "age_band"]
TARGET = "default_12m"


def _sigmoid(value: np.ndarray) -> np.ndarray:
    return 1.0 / (1.0 + np.exp(-np.clip(value, -30, 30)))


def generate_portfolio(config: dict[str, Any]) -> pd.DataFrame:
    """Generate a reproducible, privacy-safe unsecured lending portfolio."""
    cfg = config["data"]
    rows = int(cfg["rows"])
    rng = np.random.default_rng(int(cfg["seed"]))
    start = np.datetime64(cfg["start_date"])
    end = np.datetime64(cfg["end_date"])
    days = int((end - start).astype(int)) + 1
    application_date = start + rng.integers(0, days, size=rows).astype("timedelta64[D]")

    age = np.clip(np.rint(rng.normal(42, 12, rows)), 21, 74).astype(int)
    age_band = pd.cut(
        age,
        bins=[20, 29, 39, 49, 59, 74],
        labels=["21-29", "30-39", "40-49", "50-59", "60-74"],
    ).astype(str)
    gender = rng.choice(["Female", "Male"], size=rows, p=[0.50, 0.50])
    region = rng.choice(
        ["Marmara", "Central Anatolia", "Aegean", "Mediterranean", "Black Sea"],
        size=rows,
        p=[0.34, 0.22, 0.18, 0.15, 0.11],
    )
    employment_type = rng.choice(
        ["Salaried", "Self-employed", "Public sector", "Retired", "Contract"],
        size=rows,
        p=[0.50, 0.17, 0.16, 0.08, 0.09],
    )
    employment_tenure = np.clip(
        rng.gamma(2.2, 28, rows) + np.maximum(age - 30, 0) * 1.5, 0, 420
    ).round()
    base_income = np.exp(rng.normal(np.log(38_000), 0.48, rows))
    employment_multiplier = (
        pd.Series(employment_type)
        .map(
            {
                "Salaried": 1.00,
                "Self-employed": 1.18,
                "Public sector": 1.04,
                "Retired": 0.78,
                "Contract": 0.86,
            }
        )
        .to_numpy()
    )
    monthly_income = np.clip(base_income * employment_multiplier, 12_000, 260_000).round(2)
    purpose = rng.choice(
        ["Debt consolidation", "Home improvement", "Vehicle", "Education", "Medical", "Other"],
        size=rows,
        p=[0.27, 0.20, 0.19, 0.11, 0.09, 0.14],
    )
    requested_amount = np.clip(
        monthly_income * rng.lognormal(mean=-0.12, sigma=0.70, size=rows), 10_000, 750_000
    ).round(2)
    term_months = rng.choice(
        [12, 18, 24, 36, 48, 60], size=rows, p=[0.08, 0.08, 0.22, 0.31, 0.19, 0.12]
    )
    existing_debt = np.clip(monthly_income * rng.gamma(1.8, 1.5, rows), 0, 1_200_000).round(2)
    monthly_debt_payment = np.clip(
        monthly_income * rng.beta(2.0, 6.2, rows), 0, monthly_income * 0.85
    ).round(2)
    debt_to_income = np.clip(
        (monthly_debt_payment + requested_amount / np.maximum(term_months, 1)) / monthly_income,
        0,
        1.8,
    )
    credit_history_months = np.clip((age - 18) * 12 * rng.beta(3.2, 1.8, rows), 6, 660).round()
    revolving_utilization = np.clip(rng.beta(2.1, 3.0, rows), 0, 1)
    stress = 0.55 * debt_to_income + 0.50 * revolving_utilization
    delinquencies_12m = np.clip(rng.poisson(0.10 + 0.65 * stress), 0, 6)
    delinquencies_36m = np.clip(delinquencies_12m + rng.poisson(0.18 + 0.75 * stress), 0, 12)
    inquiries_6m = np.clip(rng.poisson(0.65 + 1.0 * stress), 0, 9)
    open_accounts = np.clip(rng.poisson(4.0 + np.minimum(monthly_income / 35_000, 4)), 1, 20)
    bureau_score = np.clip(
        735
        - 118 * revolving_utilization
        - 17 * delinquencies_36m
        - 8 * inquiries_6m
        + 0.07 * credit_history_months
        + rng.normal(0, 32, rows),
        300,
        850,
    ).round()
    savings_balance = np.clip(monthly_income * rng.lognormal(-0.2, 1.0, rows), 0, 1_500_000).round(
        2
    )
    current_account_balance = np.clip(
        monthly_income * rng.lognormal(-1.0, 0.9, rows), 0, 450_000
    ).round(2)
    prior_customer_months = np.clip(rng.gamma(1.8, 24, rows), 0, 240).round()
    income_verified = np.where(rng.random(rows) < 0.84, "Verified", "Unverified")
    housing_status = rng.choice(
        ["Owner", "Mortgage", "Rent", "Family"], size=rows, p=[0.24, 0.29, 0.38, 0.09]
    )
    channel = rng.choice(
        ["Mobile", "Web", "Branch", "Partner"], size=rows, p=[0.36, 0.30, 0.23, 0.11]
    )

    year = pd.DatetimeIndex(application_date).year.to_numpy()
    macro_stress = np.select(
        [year == 2022, year == 2023, year == 2024, year == 2025],
        [-0.12, 0.00, 0.11, 0.27],
        default=0.0,
    )
    purpose_effect = (
        pd.Series(purpose)
        .map(
            {
                "Debt consolidation": 0.23,
                "Home improvement": -0.06,
                "Vehicle": -0.02,
                "Education": 0.04,
                "Medical": 0.17,
                "Other": 0.09,
            }
        )
        .to_numpy()
    )
    employment_effect = (
        pd.Series(employment_type)
        .map(
            {
                "Salaried": 0.00,
                "Self-employed": 0.10,
                "Public sector": -0.20,
                "Retired": 0.03,
                "Contract": 0.23,
            }
        )
        .to_numpy()
    )
    logit = (
        -2.95
        + 1.90 * debt_to_income
        + 1.55 * revolving_utilization
        + 0.39 * delinquencies_12m
        + 0.20 * delinquencies_36m
        + 0.14 * inquiries_6m
        - 0.0072 * (bureau_score - 650)
        - 0.0018 * np.minimum(credit_history_months, 360)
        - 0.0022 * np.minimum(employment_tenure, 240)
        + 0.21 * (income_verified == "Unverified")
        + 0.13 * (channel == "Partner")
        + purpose_effect
        + employment_effect
        + macro_stress
        + rng.normal(0, 0.22, rows)
    )
    probability = _sigmoid(logit)
    default_12m = rng.binomial(1, probability)

    frame = pd.DataFrame(
        {
            "application_id": [f"APP-{idx + 1:07d}" for idx in range(rows)],
            "application_date": pd.to_datetime(application_date),
            "channel": channel,
            "region": region,
            "employment_type": employment_type,
            "employment_tenure_months": employment_tenure.astype(int),
            "monthly_income": monthly_income,
            "requested_amount": requested_amount,
            "term_months": term_months,
            "existing_debt": existing_debt,
            "monthly_debt_payment": monthly_debt_payment,
            "debt_to_income": debt_to_income.round(5),
            "credit_history_months": credit_history_months.astype(int),
            "delinquencies_12m": delinquencies_12m,
            "delinquencies_36m": delinquencies_36m,
            "revolving_utilization": revolving_utilization.round(5),
            "inquiries_6m": inquiries_6m,
            "open_accounts": open_accounts,
            "bureau_score": bureau_score.astype(int),
            "savings_balance": savings_balance,
            "current_account_balance": current_account_balance,
            "housing_status": housing_status,
            "purpose": purpose,
            "prior_customer_months": prior_customer_months.astype(int),
            "income_verified": income_verified,
            "gender": gender,
            "age_band": age_band,
            "default_12m": default_12m,
        }
    ).sort_values(["application_date", "application_id"], ignore_index=True)
    return frame


def assign_split(frame: pd.DataFrame, config: dict[str, Any]) -> pd.Series:
    """Return deterministic temporal development, validation and OOT labels."""
    development_end = pd.Timestamp(config["data"]["development_end"])
    validation_end = pd.Timestamp(config["data"]["validation_end"])
    return pd.Series(
        np.select(
            [
                frame["application_date"] <= development_end,
                frame["application_date"] <= validation_end,
            ],
            ["development", "validation"],
            default="out_of_time",
        ),
        index=frame.index,
        name="sample_split",
    )


def frame_sha256(frame: pd.DataFrame) -> str:
    """Hash canonical CSV bytes for reproducibility checks."""
    payload = frame.to_csv(index=False, date_format="%Y-%m-%d", lineterminator="\n").encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def write_portfolio(frame: pd.DataFrame, root: str | Path) -> dict[str, str]:
    """Write compressed full data and reviewer-friendly samples."""
    root_path = Path(root)
    full_path = root_path / "artifacts/data/synthetic_loan_applications.csv.gz"
    sample_path = root_path / "data/samples/loan_applications_sample.csv"
    full_path.parent.mkdir(parents=True, exist_ok=True)
    sample_path.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(
        full_path, index=False, compression={"method": "gzip", "compresslevel": 9, "mtime": 0}
    )
    frame.head(250).to_csv(sample_path, index=False, date_format="%Y-%m-%d")
    return {"full": str(full_path), "sample": str(sample_path)}
