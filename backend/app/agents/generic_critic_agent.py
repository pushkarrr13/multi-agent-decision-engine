from typing import Any

from .base_agent import BaseAgent
from ..services.llm_service import LLMService
from ..schemas.decision_response import AgentFinding, AgentResult


class GenericCriticAgent(BaseAgent):
    """
    Gemini-powered generic Critic Agent.

    Reviews the Evidence Agent and specialist-agent outputs
    before final synthesis.

    The critic is domain-neutral.
    """

    name = "critic_agent"

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
                            "Critic Agent did not receive "
                            "a business question."
                        )
                    )
                ]
            )

        # ============================================================
        # PREPARE AGENT RESULTS
        # ============================================================

        serialized_agents = []

        for agent in agent_results:

            if agent.agent_name in {
                "question_router_agent",
                "critic_agent",
            }:
                continue

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
        # REQUIRE EVIDENCE / SPECIALIST OUTPUT
        # ============================================================

        if not serialized_agents:

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
                            "No evidence or specialist results "
                            "were available for critical review."
                        )
                    )
                ]
            )

        # ============================================================
        # GEMINI CRITIQUE
        # ============================================================

        try:

            critique = (
                self.llm_service.critique_business_question(
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
                        factor="critique_error",
                        value=str(e),
                        impact="negative",
                        reason=(
                            "Gemini critic analysis failed."
                        )
                    )
                ]
            )

        # ============================================================
        # EXTRACT CRITIQUE
        # ============================================================

        status = str(
            critique.get(
                "status",
                "REVIEW"
            )
        ).upper()

        overall_assessment = str(
            critique.get(
                "overall_assessment",
                ""
            )
        ).strip()

        conflicts = critique.get(
            "conflicts",
            []
        )

        complementary_findings = critique.get(
            "complementary_findings",
            []
        )

        evidence_gaps = critique.get(
            "evidence_gaps",
            []
        )

        reasoning_issues = critique.get(
            "reasoning_issues",
            []
        )

        confidence = critique.get(
            "confidence",
            0.0
        )

        # ============================================================
        # NORMALIZE VALUES
        # ============================================================

        if not isinstance(
            conflicts,
            list
        ):
            conflicts = []

        if not isinstance(
            complementary_findings,
            list
        ):
            complementary_findings = []

        if not isinstance(
            evidence_gaps,
            list
        ):
            evidence_gaps = []

        if not isinstance(
            reasoning_issues,
            list
        ):
            reasoning_issues = []

        try:

            confidence = float(
                confidence
            )

        except (
            TypeError,
            ValueError
        ):

            confidence = 0.0

        confidence = max(
            0.0,
            min(
                1.0,
                confidence
            )
        )

        # ============================================================
        # BUILD FINDINGS
        # ============================================================

        findings = []

        # ------------------------------------------------------------
        # Overall Assessment
        # ------------------------------------------------------------

        findings.append(
            AgentFinding(
                factor="critic_assessment",
                value=overall_assessment,
                impact="positive",
                reason=(
                    "Gemini critically reviewed the "
                    "available evidence and agent outputs."
                )
            )
        )

        # ------------------------------------------------------------
        # True / Material Conflicts
        # ------------------------------------------------------------

        true_conflicts = []

        for conflict in conflicts:

            if not isinstance(
                conflict,
                dict
            ):
                continue

            conflict_type = str(
                conflict.get(
                    "type",
                    ""
                )
            ).upper()

            material = bool(
                conflict.get(
                    "material",
                    False
                )
            )

            if (
                conflict_type == "TRUE_CONFLICT"
                and material
            ):

                true_conflicts.append(
                    conflict
                )

        if true_conflicts:

            findings.append(
                AgentFinding(
                    factor="true_conflicts",
                    value=true_conflicts,
                    impact="negative",
                    reason=(
                        "Gemini identified material "
                        "disagreements between agent outputs."
                    )
                )
            )

        # ------------------------------------------------------------
        # Complementary Findings
        # ------------------------------------------------------------

        if complementary_findings:

            findings.append(
                AgentFinding(
                    factor="complementary_findings",
                    value=complementary_findings,
                    impact="positive",
                    reason=(
                        "Gemini identified agent findings "
                        "that complement rather than contradict "
                        "one another."
                    )
                )
            )

        # ------------------------------------------------------------
        # Evidence Gaps
        # ------------------------------------------------------------

        if evidence_gaps:

            for gap in evidence_gaps:

                findings.append(
                    AgentFinding(
                        factor="evidence_gap",
                        value=str(
                            gap
                        ),
                        impact="negative",
                        reason=(
                            "The critic identified missing "
                            "evidence that limits analytical reliability."
                        )
                    )
                )

        # ------------------------------------------------------------
        # Reasoning Issues
        # ------------------------------------------------------------

        if reasoning_issues:

            for issue in reasoning_issues:

                findings.append(
                    AgentFinding(
                        factor="reasoning_issue",
                        value=str(
                            issue
                        ),
                        impact="negative",
                        reason=(
                            "The critic identified a potential "
                            "reasoning problem."
                        )
                    )
                )

        # ------------------------------------------------------------
        # Confidence
        # ------------------------------------------------------------

        findings.append(
            AgentFinding(
                factor="confidence",
                value=confidence,
                impact="positive",
                reason=(
                    "Critic confidence reflects how strongly "
                    "the critical assessment is supported by "
                    "the supplied evidence and agent outputs."
                )
            )
        )

        # ============================================================
        # DETERMINE FINAL CRITIC STATUS
        # ============================================================

        material_conflict_exists = bool(
            true_conflicts
        )

        material_issue_exists = (
            material_conflict_exists
            or bool(evidence_gaps)
            or bool(reasoning_issues)
        )

        if material_issue_exists:

            final_recommendation = "REVIEW"

        else:

            final_recommendation = "PASS"

        # ============================================================
        # FINAL RESULT
        # ============================================================

        return AgentResult(
            agent_name=self.name,
            status="COMPLETED",
            score=round(
                confidence * 100,
                2
            ),
            recommendation=final_recommendation,
            findings=findings
        )