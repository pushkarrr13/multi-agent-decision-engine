from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from sqlalchemy.orm import Session

from .models_rules import BusinessRuleModel


@dataclass
class RuleEvaluation:
    rule_id: str
    rule_name: str
    matched: bool
    priority: int
    severity: str
    conditions: list[dict[str, Any]] = field(default_factory=list)
    actions: list[dict[str, Any]] = field(default_factory=list)
    reason: str = ""


SUPPORTED_OPERATORS = {
    ">",
    ">=",
    "<",
    "<=",
    "==",
    "!=",
    "IN",
    "NOT_IN",
    "CONTAINS",
    "NOT_CONTAINS",
}


def get_context_value(context: dict[str, Any], field_name: str) -> Any:
    """
    Supports both simple and nested fields.

    Examples:
        delay_rate
        metrics.delay_rate
        delivery.current.delay_rate
    """

    if field_name in context:
        return context[field_name]

    current: Any = context

    for part in field_name.split("."):
        if not isinstance(current, dict) or part not in current:
            return None

        current = current[part]

    return current


def compare_values(actual: Any, operator: str, expected: Any) -> bool:
    """
    Evaluate one condition.
    """

    operator = operator.upper()

    if operator not in SUPPORTED_OPERATORS:
        return False

    if actual is None:
        return False

    try:
        if operator == ">":
            return actual > expected

        if operator == ">=":
            return actual >= expected

        if operator == "<":
            return actual < expected

        if operator == "<=":
            return actual <= expected

        if operator == "==":
            return actual == expected

        if operator == "!=":
            return actual != expected

        if operator == "IN":
            if not isinstance(expected, list):
                expected = [expected]

            return actual in expected

        if operator == "NOT_IN":
            if not isinstance(expected, list):
                expected = [expected]

            return actual not in expected

        if operator == "CONTAINS":
            if isinstance(actual, (list, tuple, set)):
                return expected in actual

            if isinstance(actual, str):
                return str(expected).lower() in actual.lower()

            return False

        if operator == "NOT_CONTAINS":
            if isinstance(actual, (list, tuple, set)):
                return expected not in actual

            if isinstance(actual, str):
                return str(expected).lower() not in actual.lower()

            return False

    except (TypeError, ValueError):
        return False

    return False


def evaluate_condition(
    condition: dict[str, Any],
    context: dict[str, Any],
) -> tuple[bool, str]:

    field_name = condition.get("field")
    operator = condition.get("operator")
    expected = condition.get("value")

    if not field_name or not operator:
        return False, "Invalid condition definition."

    actual = get_context_value(context, field_name)

    if actual is None:
        return (
            False,
            f"Field '{field_name}' was not found in the supplied business context.",
        )

    result = compare_values(
        actual=actual,
        operator=operator,
        expected=expected,
    )

    if result:
        return (
            True,
            f"{field_name} ({actual}) {operator} {expected} → matched.",
        )

    return (
        False,
        f"{field_name} ({actual}) {operator} {expected} → not matched.",
    )


def evaluate_rule(
    rule: BusinessRuleModel,
    context: dict[str, Any],
) -> RuleEvaluation:

    conditions = rule.conditions or []

    if not conditions:
        return RuleEvaluation(
            rule_id=rule.rule_id,
            rule_name=rule.name,
            matched=True,
            priority=rule.priority,
            severity=rule.severity,
            conditions=[],
            actions=rule.actions or [],
            reason="Rule has no conditions and therefore applies automatically.",
        )

    condition_results: list[str] = []

    for condition in conditions:
        matched, reason = evaluate_condition(
            condition=condition,
            context=context,
        )

        condition_results.append(reason)

        if not matched:
            return RuleEvaluation(
                rule_id=rule.rule_id,
                rule_name=rule.name,
                matched=False,
                priority=rule.priority,
                severity=rule.severity,
                conditions=conditions,
                actions=[],
                reason="; ".join(condition_results),
            )

    return RuleEvaluation(
        rule_id=rule.rule_id,
        rule_name=rule.name,
        matched=True,
        priority=rule.priority,
        severity=rule.severity,
        conditions=conditions,
        actions=rule.actions or [],
        reason="; ".join(condition_results),
    )


def rule_applies_to_request(
    rule: BusinessRuleModel,
    business_area: str,
    question_type: str,
) -> bool:

    if not rule.enabled:
        return False

    rule_area = (rule.business_area or "GENERAL").upper()
    request_area = (business_area or "GENERAL").upper()

    if rule_area not in {"GENERAL", request_area}:
        return False

    question_types = [
        str(item).upper()
        for item in (rule.question_types or [])
    ]

    if not question_types:
        return True

    request_type = (question_type or "GENERAL").upper()

    return request_type in question_types or "ALL" in question_types


def evaluate_business_rules(
    db: Session,
    *,
    business_area: str,
    question_type: str,
    context: dict[str, Any],
) -> list[RuleEvaluation]:

    rules = (
        db.query(BusinessRuleModel)
        .filter(BusinessRuleModel.enabled.is_(True))
        .order_by(
            BusinessRuleModel.priority.asc(),
            BusinessRuleModel.id.asc(),
        )
        .all()
    )

    evaluations: list[RuleEvaluation] = []

    for rule in rules:

        if not rule_applies_to_request(
            rule=rule,
            business_area=business_area,
            question_type=question_type,
        ):
            continue

        evaluation = evaluate_rule(
            rule=rule,
            context=context,
        )

        evaluations.append(evaluation)

    return evaluations


def serialize_rule_evaluations(
    evaluations: list[RuleEvaluation],
) -> dict[str, Any]:

    matched = [
        evaluation
        for evaluation in evaluations
        if evaluation.matched
    ]

    return {
        "total_evaluated": len(evaluations),
        "matched_count": len(matched),
        "matched_rules": [
            {
                "rule_id": evaluation.rule_id,
                "rule_name": evaluation.rule_name,
                "priority": evaluation.priority,
                "severity": evaluation.severity,
                "reason": evaluation.reason,
                "actions": evaluation.actions,
            }
            for evaluation in matched
        ],
        "evaluations": [
            {
                "rule_id": evaluation.rule_id,
                "rule_name": evaluation.rule_name,
                "matched": evaluation.matched,
                "priority": evaluation.priority,
                "severity": evaluation.severity,
                "conditions": evaluation.conditions,
                "actions": evaluation.actions,
                "reason": evaluation.reason,
            }
            for evaluation in evaluations
        ],
    }