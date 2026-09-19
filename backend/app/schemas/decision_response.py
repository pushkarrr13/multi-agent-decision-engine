from typing import Any

from pydantic import BaseModel, Field


class AgentFinding(BaseModel):

    factor: str

    value: Any

    impact: str

    reason: str


class AgentResult(BaseModel):

    agent_name: str

    status: str

    score: float | None = None

    recommendation: str | None = None

    findings: list[AgentFinding] = Field(
        default_factory=list
    )


class RuleResult(BaseModel):

    rule_id: str

    rule_name: str

    description: str

    severity: str

    action: str

    triggered: bool


class DecisionExplanation(BaseModel):

    summary: str

    key_positive_factors: list[str] = Field(
        default_factory=list
    )

    key_risk_factors: list[str] = Field(
        default_factory=list
    )

    triggered_rules: list[RuleResult] = Field(
        default_factory=list
    )

    agent_conflicts: list[str] = Field(
        default_factory=list
    )

    governance_status: str

    governance_recommendation: str

    decision_score: float

    risk_score: float

    finance_score: float


class DecisionResponse(BaseModel):

    decision_id: str

    status: str

    decision: str

    requested_limit: float

    approved_limit: float | None

    confidence: float

    reasons: list[str]

    conditions: list[str]

    explanation: DecisionExplanation

    ai_analysis: str

    agents: list[AgentResult]