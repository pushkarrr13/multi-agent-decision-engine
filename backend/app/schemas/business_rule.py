from typing import Any

from pydantic import BaseModel, Field


class BusinessRuleCondition(BaseModel):
    field: str = Field(min_length=1)
    operator: str = Field(min_length=1)
    value: Any = None


class BusinessRuleAction(BaseModel):
    action_type: str = Field(min_length=1)
    value: Any = None
    message: str | None = None


class BusinessRuleCreate(BaseModel):
    name: str = Field(min_length=3, max_length=200)
    description: str = Field(min_length=3)
    business_area: str = Field(default="GENERAL")
    question_types: list[str] = Field(default_factory=list)
    priority: int = Field(default=100, ge=1)
    severity: str = Field(default="INFO")
    conditions: list[BusinessRuleCondition] = Field(
        default_factory=list
    )
    actions: list[BusinessRuleAction] = Field(
        default_factory=list
    )
    enabled: bool = True


class BusinessRuleUpdate(BaseModel):
    name: str | None = Field(
        default=None,
        min_length=3,
        max_length=200,
    )

    description: str | None = Field(
        default=None,
        min_length=3,
    )

    business_area: str | None = None

    question_types: list[str] | None = None

    priority: int | None = Field(
        default=None,
        ge=1,
    )

    severity: str | None = None

    conditions: list[BusinessRuleCondition] | None = None

    actions: list[BusinessRuleAction] | None = None

    enabled: bool | None = None


class BusinessRuleResponse(BaseModel):
    id: int
    rule_id: str
    name: str
    description: str
    business_area: str
    question_types: list[str] = Field(
        default_factory=list
    )
    priority: int
    severity: str
    conditions: list[dict[str, Any]] = Field(
        default_factory=list
    )
    actions: list[dict[str, Any]] = Field(
        default_factory=list
    )
    enabled: bool
    created_at: Any
    updated_at: Any


class BusinessRuleListResponse(BaseModel):
    total: int
    items: list[BusinessRuleResponse] = Field(
        default_factory=list
    )