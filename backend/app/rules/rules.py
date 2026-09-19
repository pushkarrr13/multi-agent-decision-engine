from dataclasses import dataclass
from typing import Any, Callable


@dataclass
class BusinessRule:
    rule_id: str
    name: str
    description: str
    severity: str
    check: Callable[[dict[str, Any]], bool]
    action: str


def check_missing_data(data: dict[str, Any]) -> bool:
    required_fields = [
        "customer_id",
        "annual_revenue",
        "existing_debt",
        "requested_credit_limit",
        "payment_history_score",
        "revenue_growth",
        "credit_utilization",
        "industry_risk",
        "customer_tenure_years",
    ]

    return any(
        field not in data or data[field] is None
        for field in required_fields
    )


def check_high_debt_ratio(data: dict[str, Any]) -> bool:
    revenue = data.get("annual_revenue", 0)
    debt = data.get("existing_debt", 0)

    if revenue <= 0:
        return True

    debt_ratio = debt / revenue

    return debt_ratio > 0.50


def check_very_high_debt_ratio(data: dict[str, Any]) -> bool:
    revenue = data.get("annual_revenue", 0)
    debt = data.get("existing_debt", 0)

    if revenue <= 0:
        return True

    debt_ratio = debt / revenue

    return debt_ratio > 0.80


def check_high_credit_utilization(
    data: dict[str, Any]
) -> bool:

    utilization = data.get(
        "credit_utilization",
        0
    )

    return utilization > 70


def check_large_credit_request(
    data: dict[str, Any]
) -> bool:

    revenue = data.get(
        "annual_revenue",
        0
    )

    requested_limit = data.get(
        "requested_credit_limit",
        0
    )

    if revenue <= 0:
        return True

    requested_ratio = (
        requested_limit / revenue
    )

    return requested_ratio > 0.50


def check_high_industry_risk(
    data: dict[str, Any]
) -> bool:

    industry_risk = str(
        data.get(
            "industry_risk",
            ""
        )
    ).lower()

    return industry_risk == "high"


# -------------------------------------------------
# Central Business Rules Registry
# -------------------------------------------------

BUSINESS_RULES = [

    BusinessRule(
        rule_id="DATA-001",
        name="Required Data Missing",
        description=(
            "All mandatory customer and financial "
            "information must be available."
        ),
        severity="CRITICAL",
        check=check_missing_data,
        action="MANUAL_REVIEW",
    ),

    BusinessRule(
        rule_id="FIN-001",
        name="High Debt to Revenue",
        description=(
            "Debt-to-revenue ratio above 50% "
            "requires additional review."
        ),
        severity="HIGH",
        check=check_high_debt_ratio,
        action="MANUAL_REVIEW",
    ),

    BusinessRule(
        rule_id="FIN-002",
        name="Very High Debt to Revenue",
        description=(
            "Debt-to-revenue ratio above 80% "
            "creates significant financial exposure."
        ),
        severity="CRITICAL",
        check=check_very_high_debt_ratio,
        action="MANUAL_REVIEW",
    ),

    BusinessRule(
        rule_id="RISK-001",
        name="High Credit Utilization",
        description=(
            "Credit utilization above 70% "
            "requires additional review."
        ),
        severity="HIGH",
        check=check_high_credit_utilization,
        action="MANUAL_REVIEW",
    ),

    BusinessRule(
        rule_id="LIMIT-001",
        name="Large Credit Request",
        description=(
            "Requested credit limit above 50% "
            "of annual revenue requires review."
        ),
        severity="HIGH",
        check=check_large_credit_request,
        action="MANUAL_REVIEW",
    ),

    BusinessRule(
        rule_id="IND-001",
        name="High Industry Risk",
        description=(
            "Customers in high-risk industries "
            "require additional review."
        ),
        severity="HIGH",
        check=check_high_industry_risk,
        action="MANUAL_REVIEW",
    ),
]