from typing import Any

from pydantic import BaseModel, Field


class BusinessAgentFinding(BaseModel):
    factor: str
    value: Any
    impact: str
    reason: str


class BusinessAgentResult(BaseModel):
    agent_name: str
    status: str

    score: float | None = None

    recommendation: str | None = None

    findings: list[BusinessAgentFinding] = Field(
        default_factory=list
    )


class RoutingResult(BaseModel):
    question_type: str
    business_area: str

    specialist_agents: list[str] = Field(
        default_factory=list
    )

    resolved_agents: list[str] = Field(
        default_factory=list
    )

    unresolved_agents: list[str] = Field(
        default_factory=list
    )


class BusinessQuestionResponse(BaseModel):
    request_id: str
    status: str

    question: str

    question_type: str
    business_area: str

    routing: RoutingResult

    agents: list[BusinessAgentResult] = Field(
        default_factory=list
    )

    answer: str | None = None

    recommendation: str | None = None

    confidence: float | None = None

    key_factors: list[str] = Field(
        default_factory=list
    )

    risks: list[str] = Field(
        default_factory=list
    )

    assumptions: list[str] = Field(
        default_factory=list
    )

    evidence: list[dict[str, Any]] = Field(
        default_factory=list
    )

    agent_conflicts: list[str] = Field(
        default_factory=list
    )

    # ------------------------------------------------------------
    # BUSINESS RULE / POLICY ENGINE
    # ------------------------------------------------------------

    business_rules: dict[str, Any] = Field(
        default_factory=dict
    )

    rule_results: dict[str, Any] = Field(
        default_factory=dict
    )

    decision_policy: dict[str, Any] = Field(
        default_factory=dict
    )