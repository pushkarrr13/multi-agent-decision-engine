from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class BusinessQuestionHistoryItem(BaseModel):
    request_id: str

    question: str

    question_type: str

    business_area: str

    status: str

    answer: str | None = None

    recommendation: str | None = None

    confidence: float | None = None

    key_factors: list[str] = Field(
        default_factory=list
    )

    created_at: datetime


class BusinessQuestionHistoryListResponse(BaseModel):
    total: int

    items: list[BusinessQuestionHistoryItem] = Field(
        default_factory=list
    )