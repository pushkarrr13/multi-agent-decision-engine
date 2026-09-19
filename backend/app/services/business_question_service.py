import uuid
from typing import Any

from sqlalchemy.orm import Session

from ..models_business import (
    BusinessQuestionRequestModel,
    BusinessAgentRunModel,
    BusinessAuditLogModel,
    BusinessDecisionResultModel,
)
from ..models_rules import BusinessRuleModel
from ..orchestration.orchestrator import DecisionOrchestrator
from ..rule_engine import evaluate_rule, serialize_rule_evaluations
from ..schemas.business_question import BusinessQuestion


class BusinessQuestionService:
    """
    Service layer for the generic business-question workflow.

    Responsibilities:

    1. Create a request ID.
    2. Persist the incoming business question.
    3. Evaluate enabled business rules before AI orchestration.
    4. Inject rule results into the orchestration context.
    5. Execute the multi-agent workflow.
    6. Re-evaluate rules after semantic routing.
    7. Apply deterministic rule actions to the final decision.
    8. Persist every agent execution.
    9. Persist the final synthesized result.
    10. Persist an auditable event trail, including rule evaluation and enforcement.

    Rule action precedence is deterministic:

        BLOCK > REQUIRE_REVIEW > ESCALATE > FLAG > SET_PRIORITY > ROUTE_TO_AGENT > NOTIFY

    For the MVP, BLOCK / REQUIRE_REVIEW / ESCALATE / FLAG are actively enforced.
    The remaining action types are recorded as policy metadata so they can be
    connected to dedicated integrations later without changing the rule model.
    """

    ACTION_PRECEDENCE = {
        "BLOCK": 100,
        "REQUIRE_REVIEW": 80,
        "ESCALATE": 70,
        "FLAG": 40,
        "SET_PRIORITY": 30,
        "ROUTE_TO_AGENT": 20,
        "NOTIFY": 10,
    }

    def __init__(self):
        self.orchestrator = DecisionOrchestrator()

    # ============================================================
    # REQUEST ID
    # ============================================================

    def _generate_request_id(self) -> str:
        return f"REQ-{uuid.uuid4().hex[:8].upper()}"

    # ============================================================
    # BUSINESS RULES
    # ============================================================

    def _load_enabled_rules(self, db: Session) -> list[BusinessRuleModel]:
        """Return enabled rules ordered by priority."""
        return (
            db.query(BusinessRuleModel)
            .filter(BusinessRuleModel.enabled.is_(True))
            .order_by(
                BusinessRuleModel.priority.asc(),
                BusinessRuleModel.id.asc(),
            )
            .all()
        )

    def _rule_scope_matches_request(
        self,
        rule: BusinessRuleModel,
        question_type: str,
        business_area: str,
    ) -> bool:
        """
        Check rule applicability from the request values.

        AUTO is treated as unresolved during the pre-orchestration pass.
        This allows the semantic router to resolve the final scope later.
        """

        request_area = str(business_area or "AUTO").upper()
        rule_area = str(rule.business_area or "GENERAL").upper()

        if request_area != "AUTO":
            if rule_area not in {"GENERAL", request_area}:
                return False

        request_type = str(question_type or "AUTO").upper()
        rule_types = [
            str(value).upper()
            for value in (rule.question_types or [])
        ]

        if request_type != "AUTO" and rule_types:
            if request_type not in rule_types and "ALL" not in rule_types:
                return False

        return True

    def _evaluate_rules_before_orchestration(
        self,
        db: Session,
        *,
        question_type: str,
        business_area: str,
        context: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Evaluate enabled business rules before the multi-agent workflow.
        """

        evaluations = []

        for rule in self._load_enabled_rules(db):
            if not self._rule_scope_matches_request(
                rule=rule,
                question_type=question_type,
                business_area=business_area,
            ):
                continue

            evaluations.append(
                evaluate_rule(
                    rule=rule,
                    context=context or {},
                )
            )

        return serialize_rule_evaluations(evaluations)

    @staticmethod
    def _coerce_routing_value(value: Any, *preferred_keys: str, default: str = "AUTO") -> str:
        """Normalize routing fields returned by the orchestrator/LLM to strings.

        Some orchestration responses may contain a structured object such as
        {"question_type": "INVESTIGATE"} instead of the plain string.
        Returning the normalized scalar prevents persistence/UI output such as
        ``[object Object]`` and allows business-rule matching to work reliably.
        """

        if value is None:
            return default

        if isinstance(value, str):
            cleaned = value.strip()
            return cleaned or default

        if isinstance(value, dict):
            for key in preferred_keys:
                nested = value.get(key)
                if nested is not None and nested is not value:
                    normalized = BusinessQuestionService._coerce_routing_value(
                        nested,
                        default=default,
                    )
                    if normalized != default:
                        return normalized

            # Handle common generic wrappers.
            for key in ("value", "name", "type", "label", "resolved"):
                nested = value.get(key)
                if nested is not None:
                    normalized = BusinessQuestionService._coerce_routing_value(
                        nested,
                        default=default,
                    )
                    if normalized != default:
                        return normalized

            return default

        # Support Pydantic-like objects without importing a concrete model.
        model_dump = getattr(value, "model_dump", None)
        if callable(model_dump):
            try:
                dumped = model_dump()
                return BusinessQuestionService._coerce_routing_value(
                    dumped,
                    *preferred_keys,
                    default=default,
                )
            except Exception:
                pass

        return str(value).strip() or default

    @classmethod
    def _normalize_routing(cls, routing: Any, request: BusinessQuestion) -> dict[str, Any]:
        """Return a frontend/API-safe routing dictionary with scalar fields."""

        if routing is None:
            routing = {}

        if not isinstance(routing, dict):
            model_dump = getattr(routing, "model_dump", None)
            if callable(model_dump):
                try:
                    routing = model_dump()
                except Exception:
                    routing = {}
            else:
                routing = {}

        normalized = dict(routing)

        normalized["question_type"] = cls._coerce_routing_value(
            routing.get("question_type"),
            "question_type",
            "type",
            default=request.question_type or "AUTO",
        ).upper()

        normalized["business_area"] = cls._coerce_routing_value(
            routing.get("business_area"),
            "business_area",
            "area",
            "domain",
            default=request.business_area or "AUTO",
        ).upper()

        # Make agent lists safe as well, avoiding object rendering in UI.
        for key in ("specialist_agents", "resolved_agents", "unresolved_agents"):
            raw_items = routing.get(key) or []
            if not isinstance(raw_items, list):
                raw_items = [raw_items]

            normalized[key] = [
                cls._coerce_routing_value(
                    item,
                    "agent_name",
                    "name",
                    "value",
                    default="",
                )
                for item in raw_items
            ]
            normalized[key] = [item for item in normalized[key] if item]

        return normalized

    def _evaluate_rules_after_routing(
        self,
        db: Session,
        *,
        question_type: str,
        business_area: str,
        context: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Re-evaluate rules using the router's resolved business area and
        question type. This is the authoritative rule result for the request.
        """

        request_area = str(business_area or "GENERAL").upper()
        request_type = str(question_type or "GENERAL").upper()

        evaluations = []

        for rule in self._load_enabled_rules(db):
            rule_area = str(rule.business_area or "GENERAL").upper()

            if rule_area not in {"GENERAL", request_area}:
                continue

            rule_types = [
                str(value).upper()
                for value in (rule.question_types or [])
            ]

            if rule_types:
                if request_type not in rule_types and "ALL" not in rule_types:
                    continue

            evaluations.append(
                evaluate_rule(
                    rule=rule,
                    context=context or {},
                )
            )

        return serialize_rule_evaluations(evaluations)

    def _audit_rule_evaluation(
        self,
        db: Session,
        *,
        request_id: str,
        phase: str,
        rule_summary: dict[str, Any],
    ) -> None:
        """Persist rule-evaluation summary in the audit trail."""

        db.add(
            BusinessAuditLogModel(
                request_id=request_id,
                event_type="BUSINESS_RULES_EVALUATED",
                agent_name="business_rule_engine",
                status="COMPLETED",
                details={
                    "phase": phase,
                    "total_evaluated": rule_summary.get(
                        "total_evaluated",
                        0,
                    ),
                    "matched_count": rule_summary.get(
                        "matched_count",
                        0,
                    ),
                    "matched_rules": rule_summary.get(
                        "matched_rules",
                        [],
                    ),
                },
            )
        )

        for matched_rule in rule_summary.get("matched_rules", []):
            db.add(
                BusinessAuditLogModel(
                    request_id=request_id,
                    event_type="BUSINESS_RULE_TRIGGERED",
                    agent_name="business_rule_engine",
                    status="TRIGGERED",
                    details={
                        "phase": phase,
                        "rule_id": matched_rule.get("rule_id"),
                        "rule_name": matched_rule.get("rule_name"),
                        "priority": matched_rule.get("priority"),
                        "severity": matched_rule.get("severity"),
                        "reason": matched_rule.get("reason"),
                        "actions": matched_rule.get("actions", []),
                    },
                )
            )

    # ============================================================
    # RULE ACTION ENFORCEMENT
    # ============================================================

    def _collect_rule_actions(
        self,
        rule_summary: dict[str, Any],
    ) -> list[dict[str, Any]]:
        """
        Flatten all actions from matched rules into one deterministic list.
        """

        actions: list[dict[str, Any]] = []

        for matched_rule in rule_summary.get("matched_rules", []):
            rule_actions = matched_rule.get("actions") or []

            for action in rule_actions:
                action_type = str(
                    action.get("action_type") or "FLAG"
                ).upper()

                actions.append(
                    {
                        "action_type": action_type,
                        "value": action.get("value"),
                        "message": action.get("message"),
                        "rule_id": matched_rule.get("rule_id"),
                        "rule_name": matched_rule.get("rule_name"),
                        "priority": matched_rule.get("priority", 100),
                        "severity": matched_rule.get("severity", "INFO"),
                        "reason": matched_rule.get("reason"),
                        "precedence": self.ACTION_PRECEDENCE.get(
                            action_type,
                            0,
                        ),
                    }
                )

        actions.sort(
            key=lambda item: (
                -int(item.get("precedence", 0)),
                int(item.get("priority", 100)),
            )
        )

        return actions

    def _apply_rule_actions(
        self,
        result: dict[str, Any],
        rule_summary: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Deterministically apply matched business-rule actions to the AI result.

        The AI is still responsible for analysis and synthesis, but configured
        policy actions can override the final recommendation when required.
        """

        actions = self._collect_rule_actions(rule_summary)

        base_recommendation = result.get("recommendation")
        base_answer = result.get("answer") or ""
        key_factors = list(result.get("key_factors") or [])
        risks = list(result.get("risks") or [])

        policy = {
            "matched": bool(actions),
            "evaluated_count": rule_summary.get("total_evaluated", 0),
            "matched_count": rule_summary.get("matched_count", 0),
            "actions_evaluated": len(actions),
            "enforced": [],
            "effective_action": None,
            "original_recommendation": base_recommendation,
            "final_recommendation": base_recommendation,
            "messages": [],
        }

        if not actions:
            result["decision_policy"] = policy
            return result

        # Apply informational / non-blocking effects first.
        for action in actions:
            action_type = action["action_type"]
            message = action.get("message") or (
                f"Rule '{action.get('rule_name')}' triggered action '{action_type}'."
            )

            policy["enforced"].append(
                {
                    "action_type": action_type,
                    "rule_id": action.get("rule_id"),
                    "rule_name": action.get("rule_name"),
                    "value": action.get("value"),
                    "severity": action.get("severity"),
                    "message": message,
                    "effective": False,
                }
            )

            policy["messages"].append(message)

            if action_type == "FLAG":
                risks.append(
                    f"Policy flag: {message}"
                )

            elif action_type == "SET_PRIORITY":
                result["policy_priority"] = action.get("value")

            elif action_type == "ROUTE_TO_AGENT":
                result["policy_route_to_agent"] = action.get("value")

            elif action_type == "NOTIFY":
                # Notification delivery is intentionally not claimed here.
                # The action is persisted so an integration can consume it later.
                result.setdefault("pending_notifications", []).append(
                    {
                        "rule_id": action.get("rule_id"),
                        "value": action.get("value"),
                        "message": message,
                    }
                )

        # Highest-precedence action determines the final policy outcome.
        effective = actions[0]
        effective_type = effective["action_type"]
        policy["effective_action"] = effective_type

        for item in policy["enforced"]:
            if (
                item["action_type"] == effective_type
                and item["rule_id"] == effective.get("rule_id")
            ):
                item["effective"] = True
                break

        effective_message = effective.get("message") or (
            f"Business policy '{effective.get('rule_name')}' requires action '{effective_type}'."
        )

        if effective_type == "BLOCK":
            result["recommendation"] = "BLOCKED"
            policy["final_recommendation"] = "BLOCKED"

            risks.insert(
                0,
                f"Decision blocked by business policy: {effective_message}",
            )

            result["answer"] = (
                f"{base_answer}\n\n"
                f"Policy enforcement: this decision was blocked because "
                f"the configured business rule '{effective.get('rule_name')}' "
                f"was triggered. {effective_message}"
            ).strip()

        elif effective_type in {"REQUIRE_REVIEW", "ESCALATE"}:
            result["recommendation"] = "MANUAL_REVIEW"
            policy["final_recommendation"] = "MANUAL_REVIEW"

            risks.insert(
                0,
                f"Manual review required by business policy: {effective_message}",
            )

            result["answer"] = (
                f"{base_answer}\n\n"
                f"Policy enforcement: human review is required because "
                f"the configured business rule '{effective.get('rule_name')}' "
                f"was triggered. {effective_message}"
            ).strip()

        elif effective_type == "FLAG":
            policy["final_recommendation"] = base_recommendation
            result["answer"] = (
                f"{base_answer}\n\n"
                f"Policy flag: {effective_message}"
            ).strip()

        result["key_factors"] = key_factors
        result["risks"] = risks
        result["decision_policy"] = policy

        return result

    def _audit_rule_actions(
        self,
        db: Session,
        *,
        request_id: str,
        policy: dict[str, Any],
    ) -> None:
        """Persist deterministic business-rule enforcement in the audit trail."""

        db.add(
            BusinessAuditLogModel(
                request_id=request_id,
                event_type="BUSINESS_RULE_ACTIONS_APPLIED",
                agent_name="business_rule_engine",
                status="COMPLETED" if policy.get("matched") else "SKIPPED",
                details=policy,
            )
        )

    # ============================================================
    # ASK BUSINESS QUESTION
    # ============================================================

    def ask(
        self,
        request: BusinessQuestion,
        db: Session,
    ) -> dict:
        """Execute and persist a generic business question."""

        request_id = self._generate_request_id()

        # --------------------------------------------------------
        # Convert request to dictionary
        # --------------------------------------------------------

        data = request.model_dump()
        data["request_id"] = request_id

        # Shared orchestration context compatibility.
        data["decision_id"] = request_id

        # Ensure context is always a dictionary for rule evaluation.
        business_context = data.get("context") or {}
        data["context"] = business_context

        # --------------------------------------------------------
        # Persist incoming request
        # --------------------------------------------------------

        request_record = BusinessQuestionRequestModel(
            request_id=request_id,
            question=request.question,
            question_type=request.question_type,
            business_area=request.business_area,
            request_data=data,
            status="PROCESSING",
        )

        db.add(request_record)
        db.flush()

        # --------------------------------------------------------
        # Audit: request started
        # --------------------------------------------------------

        db.add(
            BusinessAuditLogModel(
                request_id=request_id,
                event_type="BUSINESS_QUESTION_STARTED",
                agent_name=None,
                status="PROCESSING",
                details={
                    "question": request.question,
                    "question_type": request.question_type,
                    "business_area": request.business_area,
                },
            )
        )

        try:
            # ----------------------------------------------------
            # Evaluate business rules before orchestration
            # ----------------------------------------------------

            pre_orchestration_rules = self._evaluate_rules_before_orchestration(
                db,
                question_type=request.question_type,
                business_area=request.business_area,
                context=business_context,
            )

            # Make rule results part of the shared orchestration context.
            data["business_rules"] = pre_orchestration_rules
            data["rule_results"] = pre_orchestration_rules
            request_record.request_data = data

            self._audit_rule_evaluation(
                db,
                request_id=request_id,
                phase="PRE_ORCHESTRATION",
                rule_summary=pre_orchestration_rules,
            )

            # ----------------------------------------------------
            # Execute multi-agent workflow
            # ----------------------------------------------------

            result = self.orchestrator.execute_business_question(data)

            # ----------------------------------------------------
            # Update routed question information
            # ----------------------------------------------------

            routing = self._normalize_routing(
                result.get("routing", {}),
                request,
            )

            resolved_question_type = routing["question_type"]
            resolved_business_area = routing["business_area"]
            result["routing"] = routing

            request_record.question_type = resolved_question_type
            request_record.business_area = resolved_business_area

            # ----------------------------------------------------
            # Re-evaluate rules after semantic routing
            # ----------------------------------------------------

            post_routing_rules = self._evaluate_rules_after_routing(
                db,
                question_type=resolved_question_type,
                business_area=resolved_business_area,
                context=business_context,
            )

            data["resolved_business_rules"] = post_routing_rules
            request_record.request_data = data

            self._audit_rule_evaluation(
                db,
                request_id=request_id,
                phase="POST_ROUTING",
                rule_summary=post_routing_rules,
            )

            # ----------------------------------------------------
            # Apply deterministic rule actions
            # ----------------------------------------------------

            result["business_rules"] = post_routing_rules
            result["rule_results"] = post_routing_rules
            result = self._apply_rule_actions(
                result=result,
                rule_summary=post_routing_rules,
            )

            data["decision_policy"] = result.get("decision_policy", {})
            request_record.request_data = data

            self._audit_rule_actions(
                db,
                request_id=request_id,
                policy=result.get("decision_policy", {}),
            )

            # ----------------------------------------------------
            # Persist agent executions
            # ----------------------------------------------------

            agents = result.get("agents", [])

            for agent in agents:
                findings = [
                    finding.model_dump()
                    for finding in agent.findings
                ]

                db.add(
                    BusinessAgentRunModel(
                        request_id=request_id,
                        agent_name=agent.agent_name,
                        status=agent.status,
                        score=agent.score,
                        recommendation=agent.recommendation,
                        findings=findings,
                    )
                )

                db.add(
                    BusinessAuditLogModel(
                        request_id=request_id,
                        event_type="AGENT_COMPLETED",
                        agent_name=agent.agent_name,
                        status=agent.status,
                        details={
                            "score": agent.score,
                            "recommendation": agent.recommendation,
                            "findings": findings,
                        },
                    )
                )

            # ----------------------------------------------------
            # Persist final result
            # ----------------------------------------------------

            db.add(
                BusinessDecisionResultModel(
                    request_id=request_id,
                    answer=result.get("answer"),
                    recommendation=result.get("recommendation"),
                    confidence=result.get("confidence"),
                    key_factors=result.get("key_factors", []),
                    risks=result.get("risks", []),
                    assumptions=result.get("assumptions", []),
                    evidence=result.get("evidence", []),
                    agent_conflicts=result.get("agent_conflicts", []),
                )
            )

            # ----------------------------------------------------
            # Audit: completed
            # ----------------------------------------------------

            db.add(
                BusinessAuditLogModel(
                    request_id=request_id,
                    event_type="BUSINESS_QUESTION_COMPLETED",
                    agent_name="synthesis_agent",
                    status=result.get("status", "COMPLETED"),
                    details={
                        "question_type": resolved_question_type,
                        "business_area": resolved_business_area,
                        "recommendation": result.get("recommendation"),
                        "confidence": result.get("confidence"),
                        "key_factors": result.get("key_factors", []),
                        "risks": result.get("risks", []),
                        "matched_rules": post_routing_rules.get(
                            "matched_rules",
                            [],
                        ),
                        "decision_policy": result.get(
                            "decision_policy",
                            {},
                        ),
                    },
                )
            )

            request_record.status = result.get(
                "status",
                "COMPLETED",
            )

            db.commit()

            # ----------------------------------------------------
            # Return API response
            # ----------------------------------------------------

            return {
                "request_id": request_id,
                "status": result.get("status", "FAILED"),
                "question": request.question,
                "question_type": resolved_question_type,
                "business_area": resolved_business_area,
                "routing": routing,
                "agents": agents,
                "answer": result.get("answer"),
                "recommendation": result.get("recommendation"),
                "confidence": result.get("confidence"),
                "key_factors": result.get("key_factors", []),
                "risks": result.get("risks", []),
                "assumptions": result.get("assumptions", []),
                "evidence": result.get("evidence", []),
                "agent_conflicts": result.get("agent_conflicts", []),
                "business_rules": post_routing_rules,
                "rule_results": post_routing_rules,
                "decision_policy": result.get("decision_policy", {}),
            }

        except Exception:
            db.rollback()
            raise
