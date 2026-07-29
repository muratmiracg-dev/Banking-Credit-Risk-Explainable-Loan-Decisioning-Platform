"""API request and response contracts."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class LoanApplication(BaseModel):
    """Application-time fields accepted by the recommendation API.

    Protected attributes are intentionally absent.
    """

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    monthly_income: float = Field(gt=0, le=1_000_000)
    requested_amount: float = Field(gt=0, le=5_000_000)
    term_months: int = Field(ge=6, le=120)
    employment_tenure_months: int = Field(ge=0, le=720)
    existing_debt: float = Field(ge=0, le=10_000_000)
    monthly_debt_payment: float = Field(ge=0, le=1_000_000)
    debt_to_income: float = Field(ge=0, le=3)
    credit_history_months: int = Field(ge=0, le=840)
    delinquencies_12m: int = Field(ge=0, le=24)
    delinquencies_36m: int = Field(ge=0, le=60)
    revolving_utilization: float = Field(ge=0, le=1.5)
    inquiries_6m: int = Field(ge=0, le=30)
    open_accounts: int = Field(ge=0, le=60)
    bureau_score: int = Field(ge=300, le=850)
    savings_balance: float = Field(ge=0, le=20_000_000)
    current_account_balance: float = Field(ge=0, le=10_000_000)
    prior_customer_months: int = Field(ge=0, le=720)
    channel: Literal["Mobile", "Web", "Branch", "Partner"]
    region: Literal["Marmara", "Central Anatolia", "Aegean", "Mediterranean", "Black Sea"]
    employment_type: Literal["Salaried", "Self-employed", "Public sector", "Retired", "Contract"]
    housing_status: Literal["Owner", "Mortgage", "Rent", "Family"]
    purpose: Literal[
        "Debt consolidation",
        "Home improvement",
        "Vehicle",
        "Education",
        "Medical",
        "Other",
    ]
    income_verified: Literal["Verified", "Unverified"]


class ReasonCode(BaseModel):
    rank: int
    code: str
    feature: str
    contribution_log_odds: float
    direction: Literal["RISK_UP", "RISK_DOWN"]


class ScoreResponse(BaseModel):
    request_id: str
    model_version: str
    probability_of_default_12m: float
    credit_score: int
    risk_band: str
    recommendation: Literal["APPROVE_RECOMMENDATION", "REFER", "DECLINE_RECOMMENDATION"]
    human_review_required: bool
    illustrative_expected_loss: float
    reason_codes: list[ReasonCode]
    scope_notice: str
