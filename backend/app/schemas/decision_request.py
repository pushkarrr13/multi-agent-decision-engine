from pydantic import BaseModel, Field


class DecisionRequest(BaseModel):

    customer_id: str

    annual_revenue: float = Field(
        gt=0
    )

    existing_debt: float = Field(
        ge=0
    )

    requested_credit_limit: float = Field(
        gt=0
    )

    payment_history_score: float = Field(
        ge=0,
        le=100
    )

    revenue_growth: float

    credit_utilization: float = Field(
        ge=0,
        le=100
    )

    industry_risk: str

    customer_tenure_years: float = Field(
        ge=0
    )