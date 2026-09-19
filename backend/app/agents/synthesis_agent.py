from typing import Any

from .base_agent import BaseAgent
from ..services.llm_service import LLMService
from ..schemas.decision_response import AgentFinding, AgentResult


class SynthesisAgent(BaseAgent):
    """
    Generic final synthesis agent.

    Combines specialist-agent findings into one
    business-level answer using Gemini.
    """

    name = "synthesis_agent"

    def __init__(self):
        self.llm_service = LLMService()

    def run(
        self,
        data: dict[str, Any],
        agent_results: list
    ) -> AgentResult:

        question = str(
            data.get(
                "question",
                ""
            )
        ).strip()

        question_type = str(
            data.get(
                "question_type",
                "ANALYZE"
            )
        ).upper()

        business_area = str(
            data.get(
                "business_area",
                "GENERAL"
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
                        factor="business_question",
                        value="missing",
                        impact="negative",
                        reason=(
                            "Synthesis Agent did not receive "
                            "a business question."
                        )
                    )
                ]
            )

        # ============================================================
        # COLLECT SPECIALIST RESULTS
        # ============================================================

        usable_agents = []

        for agent in agent_results:

            if agent.agent_name in {
                "question_router_agent",
                "synthesis_agent"
            }:
                continue

            usable_agents.append(
                agent
            )

        if not usable_agents:
            return AgentResult(
                agent_name=self.name,
                status="FAILED",
                score=None,
                recommendation="MANUAL_REVIEW",
                findings=[
                    AgentFinding(
                        factor="agent_evidence",
                        value="missing",
                        impact="negative",
                        reason=(
                            "No specialist agent results were "
                            "available for synthesis."
                        )
                    )
                ]
            )

        # ============================================================
        # SERIALIZE SPECIALIST RESULTS
        # ============================================================

        serialized_agents = []

        for agent in usable_agents:

            serialized_agents.append(
                {
                    "agent_name": agent.agent_name,
                    "status": agent.status,
                    "score": agent.score,
                    "recommendation": agent.recommendation,
                    "findings": [
                        finding.model_dump()
                        for finding in agent.findings
                    ]
                }
            )

        # ============================================================
        # GEMINI SYNTHESIS
        # ============================================================

        try:

            synthesis = (
                self.llm_service.synthesize_business_question(
                    question=question,
                    question_type=question_type,
                    business_area=business_area,
                    context=context,
                    objectives=objectives,
                    constraints=constraints,
                    agent_results=serialized_agents
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
                        factor="synthesis_error",
                        value=str(e),
                        impact="negative",
                        reason=(
                            "Gemini synthesis failed. "
                            "The specialist evidence could not "
                            "be converted into a final answer."
                        )
                    )
                ]
            )

        # ============================================================
        # EXTRACT SYNTHESIS
        # ============================================================

        answer = synthesis.get(
            "answer",
            ""
        )

        recommendation = synthesis.get(
            "recommendation"
        )

        confidence = synthesis.get(
            "confidence",
            0.0
        )

        key_factors = synthesis.get(
            "key_factors",
            []
        )

        risks = synthesis.get(
            "risks",
            []
        )

        assumptions = synthesis.get(
            "assumptions",
            []
        )

        evidence = synthesis.get(
            "evidence",
            []
        )

        conflicts = synthesis.get(
            "agent_conflicts",
            []
        )

        # ============================================================
        # BUILD FINDINGS
        # ============================================================

        findings = []

        findings.append(
            AgentFinding(
                factor="answer",
                value=answer,
                impact="positive",
                reason=(
                    "Gemini synthesized the available "
                    "specialist evidence into a business answer."
                )
            )
        )

        if recommendation:
            findings.append(
                AgentFinding(
                    factor="recommendation",
                    value=recommendation,
                    impact="positive",
                    reason=(
                        "The synthesis layer produced a "
                        "recommendation from the available evidence."
                    )
                )
            )

        findings.append(
            AgentFinding(
                factor="confidence",
                value=confidence,
                impact="positive",
                reason=(
                    "Confidence reflects the completeness, "
                    "consistency and relevance of the supplied evidence."
                )
            )
        )

        findings.append(
            AgentFinding(
                factor="key_factors",
                value=key_factors,
                impact="positive",
                reason=(
                    "These are the main factors identified "
                    "by the synthesis layer."
                )
            )
        )

        if risks:
            findings.append(
                AgentFinding(
                    factor="risks",
                    value=risks,
                    impact="negative",
                    reason=(
                        "These risks were identified from "
                        "the available evidence."
                    )
                )
            )

        if assumptions:
            findings.append(
                AgentFinding(
                    factor="assumptions",
                    value=assumptions,
                    impact="negative",
                    reason=(
                        "These assumptions or information gaps "
                        "should be considered."
                    )
                )
            )

        findings.append(
            AgentFinding(
                factor="evidence",
                value=evidence,
                impact="positive",
                reason=(
                    "The synthesis output contains evidence "
                    "derived from specialist agents."
                )
            )
        )

        if conflicts:
            findings.append(
                AgentFinding(
                    factor="agent_conflicts",
                    value=conflicts,
                    impact="negative",
                    reason=(
                        "Specialist agents produced findings "
                        "that were not fully consistent."
                    )
                )
            )

        # ============================================================
        # FINAL STATUS
        # ============================================================

        if conflicts:
            final_recommendation = "REVIEW"

        elif recommendation:
            final_recommendation = "SYNTHESIZED"

        else:
            final_recommendation = "ANALYSIS_COMPLETE"

        return AgentResult(
            agent_name=self.name,
            status="COMPLETED",
            score=round(
                float(confidence) * 100,
                2
            ),
            recommendation=final_recommendation,
            findings=findings
        )