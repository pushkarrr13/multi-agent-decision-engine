from datetime import datetime

from sqlalchemy import (
    String,
    DateTime,
    JSON,
    Text,
    Float,
    ForeignKey,
)

from sqlalchemy.orm import Mapped, mapped_column

from .database import Base


class BusinessQuestionRequestModel(Base):
    """
    Stores a generic business-question request.
    """

    __tablename__ = "business_question_requests"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        autoincrement=True
    )

    request_id: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        index=True
    )

    question: Mapped[str] = mapped_column(
        Text
    )

    question_type: Mapped[str] = mapped_column(
        String(50)
    )

    business_area: Mapped[str] = mapped_column(
        String(50)
    )

    request_data: Mapped[dict] = mapped_column(
        JSON
    )

    status: Mapped[str] = mapped_column(
        String(30)
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        index=True
    )


class BusinessAgentRunModel(Base):
    """
    Stores every generic agent execution.
    """

    __tablename__ = "business_agent_runs"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        autoincrement=True
    )

    request_id: Mapped[str] = mapped_column(
        ForeignKey(
            "business_question_requests.request_id"
        ),
        index=True
    )

    agent_name: Mapped[str] = mapped_column(
        String(100)
    )

    status: Mapped[str] = mapped_column(
        String(30)
    )

    score: Mapped[float | None] = mapped_column(
        Float,
        nullable=True
    )

    recommendation: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True
    )

    findings: Mapped[list] = mapped_column(
        JSON
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        index=True
    )


class BusinessAuditLogModel(Base):
    """
    Generic audit trail for business-question processing.
    """

    __tablename__ = "business_audit_logs"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        autoincrement=True
    )

    request_id: Mapped[str] = mapped_column(
        ForeignKey(
            "business_question_requests.request_id"
        ),
        index=True
    )

    event_type: Mapped[str] = mapped_column(
        String(100)
    )

    agent_name: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True
    )

    status: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True
    )

    details: Mapped[dict] = mapped_column(
        JSON
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        index=True
    )


class BusinessDecisionResultModel(Base):
    """
    Stores the final synthesized answer.
    """

    __tablename__ = "business_decision_results"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        autoincrement=True
    )

    request_id: Mapped[str] = mapped_column(
        ForeignKey(
            "business_question_requests.request_id"
        ),
        unique=True,
        index=True
    )

    answer: Mapped[str | None] = mapped_column(
        Text,
        nullable=True
    )

    recommendation: Mapped[str | None] = mapped_column(
        Text,
        nullable=True
    )

    confidence: Mapped[float | None] = mapped_column(
        Float,
        nullable=True
    )

    key_factors: Mapped[list] = mapped_column(
        JSON
    )

    risks: Mapped[list] = mapped_column(
        JSON
    )

    assumptions: Mapped[list] = mapped_column(
        JSON
    )

    evidence: Mapped[list] = mapped_column(
        JSON
    )

    agent_conflicts: Mapped[list] = mapped_column(
        JSON
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow
    )