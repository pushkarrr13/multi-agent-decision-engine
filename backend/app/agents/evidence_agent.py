from typing import Any

from .base_agent import BaseAgent
from ..services.specialist_llm_service import SpecialistLLMService
from ..schemas.decision_response import AgentFinding, AgentResult


class EvidenceAgent(BaseAgent):
    """
    Generic evidence and data-quality agent.

    Responsibilities:

    - Inspect the supplied business context.
    - Identify available evidence.
    - Identify missing or incomplete information.
    - Determine whether the supplied data is sufficient
      for meaningful analysis.

    This agent is domain-neutral.
    """

    name = "evidence_agent"

    def __init__(self):
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
                            "No business question was supplied "
                            "for evidence analysis."
                        )
                    )
                ]
            )

        # ============================================================
        # ASK GEMINI TO REVIEW EVIDENCE
        # ============================================================

        try:

            analysis = self.llm_service.analyze(
                question=question,
                domain="Evidence and Data Quality",
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
                        factor="evidence_analysis_error",
                        value=str(e),
                        impact="negative",
                        reason=(
                            "Evidence analysis failed."
                        )
                    )
                ]
            )

        # ============================================================
        # EXTRACT RESULT
        # ============================================================

        assessment = str(
            analysis.get(
                "assessment",
                ""
            )
        ).strip()

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

        gemini_findings = analysis.get(
            "findings",
            []
        )

        if not isinstance(
            gemini_findings,
            list
        ):
            gemini_findings = []

        missing_information = analysis.get(
            "missing_information",
            []
        )

        if not isinstance(
            missing_information,
            list
        ):
            missing_information = []

        findings = []

        # ============================================================
        # EVIDENCE ASSESSMENT
        # ============================================================

        findings.append(
            AgentFinding(
                factor="evidence_assessment",
                value=assessment,
                impact="positive",
                reason=(
                    "The Evidence Agent assessed the "
                    "completeness and quality of the supplied "
                    "business information."
                )
            )
        )

        # ============================================================
        # AVAILABLE EVIDENCE
        # ============================================================

        for item in gemini_findings:

            if not isinstance(
                item,
                dict
            ):
                continue

            factor = str(
                item.get(
                    "factor",
                    "evidence_factor"
                )
            )

            value = item.get(
                "value"
            )

            reason = str(
                item.get(
                    "reason",
                    ""
                )
            )

            impact = str(
                item.get(
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

            findings.append(
                AgentFinding(
                    factor=f"evidence:{factor}",
                    value=value,
                    impact=impact,
                    reason=reason
                )
            )

        # ============================================================
        # MISSING INFORMATION
        # ============================================================

        for item in missing_information:

            findings.append(
                AgentFinding(
                    factor="missing_information",
                    value=str(
                        item
                    ),
                    impact="negative",
                    reason=(
                        "This information may be required "
                        "for stronger business analysis."
                    )
                )
            )

        # ============================================================
        # CONFIDENCE
        # ============================================================

        findings.append(
            AgentFinding(
                factor="confidence",
                value=confidence,
                impact="positive",
                reason=(
                    "Confidence reflects the quality and "
                    "completeness of the available evidence."
                )
            )
        )

        # ============================================================
        # RECOMMENDATION
        # ============================================================

        if missing_information:
            recommendation = "MORE_DATA_REQUIRED"
        else:
            recommendation = "EVIDENCE_SUFFICIENT"

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
            recommendation=recommendation,
            findings=findings
        )