from typing import Any

from pydantic import BaseModel, Field


class AnalyticsOverview(BaseModel):
    total_questions: int = 0
    completed_questions: int = 0
    failed_questions: int = 0

    average_confidence: float | None = None

    investigate_count: int = 0
    decide_count: int = 0
    recommend_count: int = 0
    analyze_count: int = 0
    compare_count: int = 0
    predict_count: int = 0
    explain_count: int = 0
    optimize_count: int = 0

    top_business_area: str | None = None


class BusinessAreaMetric(BaseModel):
    business_area: str
    question_count: int
    average_confidence: float | None = None


class QuestionTypeMetric(BaseModel):
    question_type: str
    question_count: int


class AgentMetric(BaseModel):
    agent_name: str
    run_count: int
    completed_count: int
    failed_count: int
    average_score: float | None = None


class AnalyticsResponse(BaseModel):
    overview: AnalyticsOverview

    business_areas: list[BusinessAreaMetric] = Field(
        default_factory=list
    )

    question_types: list[QuestionTypeMetric] = Field(
        default_factory=list
    )

    agents: list[AgentMetric] = Field(
        default_factory=list
    )

    recent_activity: list[dict[str, Any]] = Field(
        default_factory=list
    )