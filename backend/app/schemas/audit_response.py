from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class AuditEvent(BaseModel):

    id: int

    decision_id: str

    event_type: str

    agent_name: str | None = None

    status: str | None = None

    decision: str | None = None

    details: dict[str, Any] = Field(
        default_factory=dict
    )

    created_at: datetime


class AuditHistoryResponse(BaseModel):

    decision_id: str

    total_events: int

    events: list[AuditEvent] = Field(
        default_factory=list
    )