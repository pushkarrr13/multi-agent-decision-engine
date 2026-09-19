from datetime import datetime

from sqlalchemy import (
    String,
    Float,
    DateTime,
    ForeignKey,
    JSON,
    Text
)

from sqlalchemy.orm import Mapped, mapped_column

from .database import Base


# =========================================================
# Decision Request
# =========================================================

class DecisionRequestModel(Base):

    __tablename__ = "decision_requests"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        autoincrement=True
    )

    decision_id: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        index=True
    )

    customer_id: Mapped[str] = mapped_column(
        String(100),
        index=True
    )

    request_data: Mapped[dict] = mapped_column(
        JSON
    )

    status: Mapped[str] = mapped_column(
        String(30)
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow
    )


# =========================================================
# Agent Run
# =========================================================

class AgentRunModel(Base):

    __tablename__ = "agent_runs"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        autoincrement=True
    )

    decision_id: Mapped[str] = mapped_column(
        ForeignKey(
            "decision_requests.decision_id"
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
        String(100),
        nullable=True
    )

    findings: Mapped[list] = mapped_column(
        JSON
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow
    )


# =========================================================
# Final Decision
# =========================================================

class DecisionModel(Base):

    __tablename__ = "decisions"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        autoincrement=True
    )

    decision_id: Mapped[str] = mapped_column(
        ForeignKey(
            "decision_requests.decision_id"
        ),
        unique=True
    )

    decision: Mapped[str] = mapped_column(
        String(100)
    )

    requested_limit: Mapped[float] = mapped_column(
        Float
    )

    approved_limit: Mapped[float | None] = mapped_column(
        Float,
        nullable=True
    )

    confidence: Mapped[float] = mapped_column(
        Float
    )

    reasons: Mapped[list] = mapped_column(
        JSON
    )

    conditions: Mapped[list] = mapped_column(
        JSON
    )

    ai_analysis: Mapped[str | None] = mapped_column(
        Text,
        nullable=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow
    )


# =========================================================
# Audit Log
# =========================================================

class AuditLogModel(Base):

    __tablename__ = "audit_logs"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        autoincrement=True
    )

    decision_id: Mapped[str] = mapped_column(
        ForeignKey(
            "decision_requests.decision_id"
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

    decision: Mapped[str | None] = mapped_column(
        String(100),
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