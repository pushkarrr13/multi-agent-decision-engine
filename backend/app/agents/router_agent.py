from typing import Any

from .base_agent import BaseAgent
from ..services.llm_service import LLMService
from ..schemas.decision_response import AgentFinding, AgentResult


class QuestionRouterAgent(BaseAgent):
    """
    Generic business-question router.

    Uses Gemini to semantically determine:

    - question type
    - business area
    - relevant specialist agents

    Evidence validation is a core part of the generic workflow.
    """

    name = "question_router_agent"

    CORE_AGENTS = [
        "evidence_agent",
    ]

    def __init__(self):
        self.llm_service = LLMService()

    def run(
        self,
        data: dict[str, Any]
    ) -> AgentResult:

        question = str(
            data.get(
                "question",
                ""
            )
        ).strip()

        supplied_question_type = str(
            data.get(
                "question_type",
                "AUTO"
            )
        ).upper()

        supplied_business_area = str(
            data.get(
                "business_area",
                "AUTO"
            )
        ).upper()

        context = data.get(
            "context",
            {}
        )

        objectives = data.get(
            "objectives",
            []
        )

        constraints = data.get(
            "constraints",
            []
        )

        # ============================================================
        # VALIDATE QUESTION
        # ============================================================

        if not question:
            return AgentResult(
                agent_name=self.name,
                status="FAILED",
                score=None,
                recommendation="MANUAL_REVIEW",
                findings=[
                    AgentFinding(
                        factor="question",
                        value="missing",
                        impact="negative",
                        reason=(
                            "No business question was provided "
                            "to the Question Router."
                        )
                    )
                ]
            )

        # ============================================================
        # GEMINI SEMANTIC ROUTING
        # ============================================================

        try:
            routing_result = (
                self.llm_service.route_business_question(
                    question=question,
                    question_type=supplied_question_type,
                    business_area=supplied_business_area,
                    context=context,
                    objectives=objectives,
                    constraints=constraints,
                )
            )

        except Exception as e:
            return AgentResult(
                agent_name=self.name,
                status="FAILED",
                score=None,
                recommendation="MANUAL_REVIEW",
                findings=[
                    AgentFinding(
                        factor="routing_error",
                        value=str(e),
                        impact="negative",
                        reason=(
                            "Gemini semantic routing failed."
                        )
                    )
                ]
            )

        question_type = routing_result.get(
            "question_type",
            "ANALYZE"
        )

        business_area = routing_result.get(
            "business_area",
            "GENERAL"
        )

        specialist_agents = routing_result.get(
            "specialist_agents",
            []
        )

        reasoning = routing_result.get(
            "reasoning",
            ""
        )

        # ============================================================
        # BUILD COMPLETE AGENT SELECTION
        # ============================================================

        selected_agents = []

        for agent_name in self.CORE_AGENTS:

            if agent_name not in selected_agents:
                selected_agents.append(
                    agent_name
                )

        for agent_name in specialist_agents:

            if agent_name not in selected_agents:
                selected_agents.append(
                    agent_name
                )

        # ============================================================
        # ROUTER FINDINGS
        # ============================================================

        findings = []

        findings.append(
            AgentFinding(
                factor="question_type",
                value={
                    "value": question_type,
                    "source": "gemini"
                },
                impact="positive",
                reason=(
                    f"Gemini classified the business "
                    f"question as {question_type}."
                )
            )
        )

        findings.append(
            AgentFinding(
                factor="business_area",
                value={
                    "value": business_area,
                    "source": "gemini"
                },
                impact="positive",
                reason=(
                    f"Gemini classified the business area "
                    f"as {business_area}."
                )
            )
        )

        findings.append(
            AgentFinding(
                factor="specialist_agents",
                value=specialist_agents,
                impact="positive",
                reason=(
                    "Gemini selected the specialist agents "
                    "relevant to the business question."
                )
            )
        )

        findings.append(
            AgentFinding(
                factor="core_agents",
                value=self.CORE_AGENTS,
                impact="positive",
                reason=(
                    "Evidence validation is a core part "
                    "of every generic business workflow."
                )
            )
        )

        findings.append(
            AgentFinding(
                factor="selected_agents",
                value=selected_agents,
                impact="positive",
                reason=(
                    "The final initial agent set contains "
                    "the evidence agent and Gemini-selected "
                    "specialists."
                )
            )
        )

        findings.append(
            AgentFinding(
                factor="routing_reasoning",
                value=reasoning,
                impact="positive",
                reason=(
                    "Gemini provided the reasoning behind "
                    "the selected routing."
                )
            )
        )

        # ============================================================
        # FINAL RESULT
        # ============================================================

        return AgentResult(
            agent_name=self.name,
            status="COMPLETED",
            score=None,
            recommendation="ROUTE",
            findings=findings
        )