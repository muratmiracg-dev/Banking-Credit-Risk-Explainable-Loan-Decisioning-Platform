"""API request and response contracts."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

# The training data derive debt_to_income from the other affordability fields and cap it
# at this value; a request must carry the same derivation.
DEBT_TO_INCOME_CAP = 1.8
DEBT_TO_INCOME_TOLERANCE = 0.005


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

    @model_validator(mode="after")
    def _check_derived_fields(self) -> LoanApplication:
        # debt_to_income is the model's strongest affordability driver but is fully
        # determined by income, existing payments and the new instalment. Accepting it
        # as an independent number let a caller send 0.05 alongside payments that imply
        # 0.90 and receive an approval recommendation.
        implied = min(
            (self.monthly_debt_payment + self.requested_amount / self.term_months)
            / self.monthly_income,
            DEBT_TO_INCOME_CAP,
        )
        if abs(self.debt_to_income - implied) > DEBT_TO_INCOME_TOLERANCE:
            raise ValueError(
                "debt_to_income must equal (monthly_debt_payment + requested_amount / "
                f"term_months) / monthly_income, capped at {DEBT_TO_INCOME_CAP}; "
                f"expected {implied:.4f}, received {self.debt_to_income:.4f}"
            )
        if self.delinquencies_12m > self.delinquencies_36m:
            raise ValueError("delinquencies_12m cannot exceed delinquencies_36m")
        return self


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
