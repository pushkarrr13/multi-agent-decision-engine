import uuid

from sqlalchemy.orm import Session

from ..models import (
    DecisionRequestModel,
    AgentRunModel,
    DecisionModel,
    AuditLogModel
)

from ..orchestration.orchestrator import (
    DecisionOrchestrator
)


class DecisionService:

    def __init__(self):

        self.orchestrator = DecisionOrchestrator()

    def make_decision(
        self,
        request,
        db: Session
    ):

        try:

            # ---------------------------------------------
            # 1. Prepare Decision Request
            # ---------------------------------------------

            data = request.model_dump()

            decision_id = (
                f"DEC-{uuid.uuid4().hex[:8].upper()}"
            )

            data["decision_id"] = decision_id

            # ---------------------------------------------
            # 2. Create Initial Decision Request
            # ---------------------------------------------

            decision_request = DecisionRequestModel(
                decision_id=decision_id,
                customer_id=request.customer_id,
                request_data=data,
                status="PROCESSING"
            )

            db.add(decision_request)

            db.flush()

            # ---------------------------------------------
            # 3. Audit - Decision Started
            # ---------------------------------------------

            db.add(
                AuditLogModel(
                    decision_id=decision_id,
                    event_type="DECISION_STARTED",
                    agent_name=None,
                    status="PROCESSING",
                    decision=None,
                    details={
                        "customer_id": (
                            request.customer_id
                        ),
                        "requested_limit": (
                            request.requested_credit_limit
                        )
                    }
                )
            )

            # ---------------------------------------------
            # 4. Execute Multi-Agent Decision
            # ---------------------------------------------

            result = self.orchestrator.execute(
                data
            )

            # ---------------------------------------------
            # 5. Save Agent Results
            # ---------------------------------------------

            for agent in result["agents"]:

                findings = [
                    finding.model_dump()
                    for finding in agent.findings
                ]

                # Save agent execution
                agent_run = AgentRunModel(
                    decision_id=decision_id,
                    agent_name=agent.agent_name,
                    status=agent.status,
                    score=agent.score,
                    recommendation=(
                        agent.recommendation
                    ),
                    findings=findings
                )

                db.add(agent_run)

                # -----------------------------------------
                # Audit - Agent Completed
                # -----------------------------------------

                db.add(
                    AuditLogModel(
                        decision_id=decision_id,
                        event_type="AGENT_COMPLETED",
                        agent_name=agent.agent_name,
                        status=agent.status,
                        decision=None,
                        details={
                            "score": agent.score,
                            "recommendation": (
                                agent.recommendation
                            ),
                            "findings": findings
                        }
                    )
                )

            # ---------------------------------------------
            # 6. Audit - Business Rules
            # ---------------------------------------------

            explanation = result.get(
                "explanation"
            )

            triggered_rules = []

            if explanation is not None:

                triggered_rules = [
                    rule.model_dump()
                    for rule
                    in explanation.triggered_rules
                ]

            for rule in triggered_rules:

                db.add(
                    AuditLogModel(
                        decision_id=decision_id,
                        event_type="RULE_TRIGGERED",
                        agent_name="governance_agent",
                        status="FAILED",
                        decision=None,
                        details={
                            "rule_id": (
                                rule["rule_id"]
                            ),
                            "rule_name": (
                                rule["rule_name"]
                            ),
                            "severity": (
                                rule["severity"]
                            ),
                            "action": (
                                rule["action"]
                            ),
                            "description": (
                                rule["description"]
                            )
                        }
                    )
                )

            # ---------------------------------------------
            # 7. Audit - Governance Review
            # ---------------------------------------------

            if explanation is not None:

                db.add(
                    AuditLogModel(
                        decision_id=decision_id,
                        event_type="GOVERNANCE_REVIEW",
                        agent_name="governance_agent",
                        status=(
                            explanation.governance_status
                        ),
                        decision=None,
                        details={
                            "recommendation": (
                                explanation
                                .governance_recommendation
                            ),
                            "triggered_rule_count": (
                                len(
                                    explanation
                                    .triggered_rules
                                )
                            ),
                            "critical_rules_triggered": (
                                any(
                                    rule.severity
                                    == "CRITICAL"
                                    for rule
                                    in explanation
                                    .triggered_rules
                                )
                            )
                        }
                    )
                )

            # ---------------------------------------------
            # 8. Audit - Critic Review
            # ---------------------------------------------

            critic_agent = None

            for agent in result["agents"]:

                if agent.agent_name == "critic_agent":

                    critic_agent = agent

                    break

            if critic_agent is not None:

                db.add(
                    AuditLogModel(
                        decision_id=decision_id,
                        event_type="CRITIC_REVIEW",
                        agent_name="critic_agent",
                        status=(
                            critic_agent.status
                        ),
                        decision=None,
                        details={
                            "recommendation": (
                                critic_agent
                                .recommendation
                            ),
                            "findings": [
                                finding.model_dump()
                                for finding
                                in critic_agent.findings
                            ]
                        }
                    )
                )

            # ---------------------------------------------
            # 9. Save Final Decision
            # ---------------------------------------------

            final_decision = DecisionModel(
                decision_id=decision_id,
                decision=result["decision"],
                requested_limit=(
                    request.requested_credit_limit
                ),
                approved_limit=(
                    result["approved_limit"]
                ),
                confidence=(
                    result["confidence"]
                ),
                reasons=(
                    result["reasons"]
                ),
                conditions=(
                    result["conditions"]
                ),
                ai_analysis=(
                    result["ai_analysis"]
                )
            )

            db.add(final_decision)

            # ---------------------------------------------
            # 10. Update Request Status
            # ---------------------------------------------

            decision_request.status = (
                "COMPLETED"
            )

            # ---------------------------------------------
            # 11. Audit - Final Decision
            # ---------------------------------------------

            db.add(
                AuditLogModel(
                    decision_id=decision_id,
                    event_type="DECISION_COMPLETED",
                    agent_name="decision_agent",
                    status="COMPLETED",
                    decision=(
                        result["decision"]
                    ),
                    details={
                        "requested_limit": (
                            request
                            .requested_credit_limit
                        ),
                        "approved_limit": (
                            result["approved_limit"]
                        ),
                        "confidence": (
                            result["confidence"]
                        ),
                        "reasons": (
                            result["reasons"]
                        ),
                        "conditions": (
                            result["conditions"]
                        )
                    }
                )
            )

            # ---------------------------------------------
            # 12. Commit Everything
            # ---------------------------------------------

            db.commit()

            # ---------------------------------------------
            # 13. Return API Response
            # ---------------------------------------------

            return {
                "decision_id": decision_id,

                "status": "COMPLETED",

                "decision": (
                    result["decision"]
                ),

                "requested_limit": (
                    request.requested_credit_limit
                ),

                "approved_limit": (
                    result["approved_limit"]
                ),

                "confidence": (
                    result["confidence"]
                ),

                "reasons": (
                    result["reasons"]
                ),

                "conditions": (
                    result["conditions"]
                ),

                "explanation": (
                    result["explanation"]
                ),

                "ai_analysis": (
                    result["ai_analysis"]
                ),

                "agents": (
                    result["agents"]
                )
            }

        except Exception:

            db.rollback()

            raise