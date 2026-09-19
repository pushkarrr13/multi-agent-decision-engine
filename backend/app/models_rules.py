from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    Integer,
    JSON,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column

from .database import Base


class BusinessRuleModel(Base):
    __tablename__ = "business_rules"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )

    rule_id: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        index=True,
    )

    name: Mapped[str] = mapped_column(
        String(200),
    )

    description: Mapped[str] = mapped_column(
        Text,
    )

    business_area: Mapped[str] = mapped_column(
        String(50),
        index=True,
    )

    question_types: Mapped[list] = mapped_column(
        JSON,
        default=list,
    )

    priority: Mapped[int] = mapped_column(
        Integer,
        default=100,
    )

    severity: Mapped[str] = mapped_column(
        String(30),
        default="INFO",
    )

    conditions: Mapped[list] = mapped_column(
        JSON,
        default=list,
    )

    actions: Mapped[list] = mapped_column(
        JSON,
        default=list,
    )

    enabled: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        index=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        index=True,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )