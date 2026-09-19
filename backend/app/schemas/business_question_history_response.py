from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class BusinessAgentRunHistory(BaseModel):
    id: int
    request_id: str
    agent_name: str
    status: str
    score: float | None = None
    recommendation: str | None = None
    findings: list[dict[str, Any]] = Field(
        default_factory=list
    )
    created_at: datetime


class BusinessAuditHistory(BaseModel):
    id: int
    request_id: str
    event_type: str
    agent_name: str | None = None
    status: str | None = None
    details: dict[str, Any] = Field(
        default_factory=dict
    )
    created_at: datetime


class BusinessDecisionHistory(BaseModel):
    request_id: str
    question: str
    question_type: str
    business_area: str
    status: str
    request_data: dict[str, Any] = Field(
        default_factory=dict
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

    created_at: datetime

    agents: list[BusinessAgentRunHistory] = Field(
        default_factory=list
    )

    audit_events: list[BusinessAuditHistory] = Field(
        default_factory=list
    )