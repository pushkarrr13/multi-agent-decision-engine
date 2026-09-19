from typing import Any

from .base_agent import BaseAgent
from ..services.specialist_llm_service import SpecialistLLMService
from ..schemas.decision_response import AgentFinding, AgentResult


class SpecialistAgent(BaseAgent):
    """
    Generic Gemini-powered specialist agent.

    The same implementation supports different domains such as:
    Finance, Operations, Product, Procurement, Customer, etc.
    """

    name = "specialist_agent"

    def __init__(
        self,
        specialist_name: str,
        domain: str
    ):
        self.name = specialist_name
        self.domain = domain

        self.llm_service = SpecialistLLMService()

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
                            "The specialist agent did not "
                            "receive a business question."
                        )
                    )
                ]
            )

        # ============================================================
        # GEMINI ANALYSIS
        # ============================================================

        try:
            analysis = self.llm_service.analyze(
                question=question,
                domain=self.domain,
                context=context,
                objectives=objectives,
                constraints=constraints
            )

        except Exception as e:
            return AgentResult(
                agent_name=self.name,
                status="FAILED",
                score=None,
                recommendation="MANUAL_REVIEW",
                findings=[
                    AgentFinding(
                        factor="analysis_error",
                        value=str(e),
                        impact="negative",
                        reason=(
                            f"{self.domain} specialist "
                            "analysis failed."
                        )
                    )
                ]
            )

        # ============================================================
        # EXTRACT GEMINI RESULT
        # ============================================================

        assessment = str(
            analysis.get(
                "assessment",
                ""
            )
        ).strip()

        recommendation_value = analysis.get(
            "recommendation"
        )

        if recommendation_value is None:
            recommendation = None
        else:
            recommendation = str(
                recommendation_value
            ).strip()

            if not recommendation:
                recommendation = None

        confidence = analysis.get(
            "confidence",
            0.0
        )

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
        # Domain Assessment
        # ------------------------------------------------------------

        findings.append(
            AgentFinding(
                factor="domain_assessment",
                value=assessment,
                impact="positive",
                reason=(
                    f"{self.domain} specialist produced "
                    "a domain-specific assessment."
                )
            )
        )

        # ------------------------------------------------------------
        # Gemini Findings
        # ------------------------------------------------------------

        gemini_findings = analysis.get(
            "findings",
            []
        )

        if not isinstance(
            gemini_findings,
            list
        ):
            gemini_findings = []

        for finding in gemini_findings:

            if not isinstance(
                finding,
                dict
            ):
                continue

            factor = str(
                finding.get(
                    "factor",
                    "specialist_factor"
                )
            )

            value = finding.get(
                "value"
            )

            impact = str(
                finding.get(
                    "impact",
                    "neutral"
                )
            ).lower()

            if impact not in {
                "positive",
                "negative",
                "neutral"
            }:
                impact = "neutral"

            reason = str(
                finding.get(
                    "reason",
                    ""
                )
            )

            findings.append(
                AgentFinding(
                    factor=(
                        f"{self.domain.lower()}:{factor}"
                    ),
                    value=value,
                    impact=impact,
                    reason=reason
                )
            )

        # ------------------------------------------------------------
        # Missing Information
        # ------------------------------------------------------------

        missing_information = analysis.get(
            "missing_information",
            []
        )

        if not isinstance(
            missing_information,
            list
        ):
            missing_information = []

        for item in missing_information:

            findings.append(
                AgentFinding(
                    factor="missing_information",
                    value=str(item),
                    impact="negative",
                    reason=(
                        f"{self.domain} specialist identified "
                        "information needed for stronger analysis."
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
                    f"Confidence represents how strongly "
                    f"the supplied evidence supports the "
                    f"{self.domain} assessment."
                )
            )
        )

        # ============================================================
        # FINAL RESULT
        # ============================================================

        if recommendation:
            final_recommendation = recommendation
        else:
            final_recommendation = "ANALYZE"

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