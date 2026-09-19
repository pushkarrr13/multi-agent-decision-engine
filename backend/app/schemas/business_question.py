from typing import Any

from pydantic import BaseModel, Field


class BusinessQuestion(BaseModel):
    """
    Generic input contract for the Multi-Agent Business Decision Engine.

    The engine is not tied to a specific business domain such as
    credit, finance, sales, operations, or pricing.
    """

    question: str = Field(
        min_length=5,
        description="The business question the user wants the engine to answer."
    )

    question_type: str = Field(
        default="AUTO",
        description=(
            "Type of business question. "
            "Examples: ANALYZE, COMPARE, INVESTIGATE, "
            "PREDICT, RECOMMEND, DECIDE, EXPLAIN, OPTIMIZE, AUTO."
        )
    )

    business_area: str = Field(
        default="AUTO",
        description=(
            "Business domain. "
            "Examples: FINANCE, SALES, MARKETING, "
            "OPERATIONS, PRODUCT, HR, PROCUREMENT, STRATEGY, AUTO."
        )
    )

    context: dict[str, Any] = Field(
        default_factory=dict,
        description="Additional structured business context."
    )

    objectives: list[str] = Field(
        default_factory=list,
        description="Business objectives the analysis should consider."
    )

    constraints: list[str] = Field(
        default_factory=list,
        description="Business constraints or limitations."
    )

    data_sources: list[dict[str, Any]] = Field(
        default_factory=list,
        description="Optional datasets or external/internal data references."
    )

    success_criteria: list[str] = Field(
        default_factory=list,
        description="Criteria that define a useful business outcome."
    )

    requested_output: str = Field(
        default="RECOMMENDATION",
        description=(
            "Desired output format. "
            "Examples: ANSWER, ANALYSIS, RECOMMENDATION, "
            "DECISION, COMPARISON, INVESTIGATION."
        )
    )