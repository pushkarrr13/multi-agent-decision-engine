from typing import Any

from ..agents.data_agent import DataAgent
from ..agents.risk_agent import RiskAgent
from ..agents.finance_agent import FinanceAgent
from ..agents.governance_agent import GovernanceAgent
from ..agents.decision_agent import DecisionAgent
from ..agents.critic_agent import CriticAgent

from ..agents.router_agent import QuestionRouterAgent
from ..agents.specialist_registry import SpecialistRegistry
from ..agents.synthesis_agent import SynthesisAgent
from ..agents.evidence_agent import EvidenceAgent
from ..agents.generic_critic_agent import GenericCriticAgent

from .context import DecisionContext


class DecisionOrchestrator:
    """
    Main orchestration layer.

    Generic workflow:

    Business Question
            ↓
    Question Router
            ↓
    Evidence Agent
            ↓
    Dynamic Specialists
            ↓
    Generic Critic
            ↓
    Synthesis Agent
            ↓
    Final Business Answer

    Legacy credit workflow remains available temporarily.
    """

    def __init__(self):

        # ============================================================
        # LEGACY CREDIT WORKFLOW
        # ============================================================

        self.data_agent = DataAgent()

        self.risk_agent = RiskAgent()

        self.finance_agent = FinanceAgent()

        self.governance_agent = GovernanceAgent()

        self.decision_agent = DecisionAgent()

        # IMPORTANT:
        # This is the OLD credit-specific critic.
        self.critic_agent = CriticAgent()

        # ============================================================
        # GENERIC BUSINESS WORKFLOW
        # ============================================================

        self.question_router = (
            QuestionRouterAgent()
        )

        self.evidence_agent = (
            EvidenceAgent()
        )

        self.specialist_registry = (
            SpecialistRegistry()
        )

        # IMPORTANT:
        # Generic business critic.
        self.generic_critic_agent = (
            GenericCriticAgent()
        )

        self.synthesis_agent = (
            SynthesisAgent()
        )

    # ================================================================
    # GENERIC BUSINESS QUESTION WORKFLOW
    # ================================================================

    def execute_business_question(
        self,
        data: dict[str, Any]
    ) -> dict[str, Any]:
        """
        Execute the generic business-question workflow.

        The Critic runs BEFORE synthesis so that its findings
        become part of the evidence supplied to the Synthesis Agent.
        """

        context = DecisionContext(
            decision_id=data.get(
                "decision_id",
                "PENDING"
            ),
            input_data=data
        )

        # ============================================================
        # 1. QUESTION ROUTER
        # ============================================================

        router_result = (
            self.question_router.run(
                data
            )
        )

        context.add_agent_result(
            router_result
        )

        if router_result.status != "COMPLETED":

            return {
                "status": "FAILED",
                "routing": {},
                "agents": context.agent_results,
                "answer": None,
                "recommendation": None,
                "confidence": None,
                "key_factors": [],
                "risks": [],
                "assumptions": [],
                "evidence": [],
                "agent_conflicts": []
            }

        # ============================================================
        # 2. EXTRACT ROUTING INFORMATION
        # ============================================================

        question_type = (
            self._get_routing_value(
                router_result,
                "question_type"
            )
        )

        business_area = (
            self._get_routing_value(
                router_result,
                "business_area"
            )
        )

        specialist_names = (
            self._get_routing_list(
                router_result,
                "specialist_agents"
            )
        )

        # ============================================================
        # 3. EVIDENCE AGENT
        # ============================================================

        evidence_result = (
            self.evidence_agent.run(
                data,
                context.agent_results
            )
        )

        context.add_agent_result(
            evidence_result
        )

        # ============================================================
        # 4. RESOLVE SPECIALISTS
        # ============================================================

        specialists = (
            self.specialist_registry.get_many(
                specialist_names
            )
        )

        resolved_agent_names = [
            specialist.name
            for specialist in specialists
        ]

        # ============================================================
        # 5. EXECUTE SPECIALISTS DYNAMICALLY
        # ============================================================

        for specialist in specialists:

            result = specialist.run(
                data,
                context.agent_results
            )

            context.add_agent_result(
                result
            )

        # ============================================================
        # 6. DETECT UNRESOLVED SPECIALISTS
        # ============================================================

        unresolved_agents = [
            agent_name
            for agent_name in specialist_names
            if agent_name not in resolved_agent_names
        ]

        # ============================================================
        # 7. GENERIC CRITIC
        # ============================================================

        critic_result = (
            self.generic_critic_agent.run(
                data,
                context.agent_results
            )
        )

        context.add_agent_result(
            critic_result
        )

        # ============================================================
        # 8. SYNTHESIS INPUT
        # ============================================================

        synthesis_data = {
            **data,
            "question_type": question_type,
            "business_area": business_area
        }

        # ============================================================
        # 9. SYNTHESIS
        # ============================================================

        synthesis_result = (
            self.synthesis_agent.run(
                synthesis_data,
                context.agent_results
            )
        )

        context.add_agent_result(
            synthesis_result
        )

        # ============================================================
        # 10. EXTRACT SYNTHESIS OUTPUT
        # ============================================================

        answer = self._get_agent_finding(
            synthesis_result,
            "answer"
        )

        recommendation = self._get_agent_finding(
            synthesis_result,
            "recommendation"
        )

        confidence = self._get_agent_finding(
            synthesis_result,
            "confidence"
        )

        key_factors = self._get_agent_finding(
            synthesis_result,
            "key_factors"
        )

        risks = self._get_agent_finding(
            synthesis_result,
            "risks"
        )

        assumptions = self._get_agent_finding(
            synthesis_result,
            "assumptions"
        )

        evidence = self._get_agent_finding(
            synthesis_result,
            "evidence"
        )

        agent_conflicts = self._get_agent_finding(
            synthesis_result,
            "agent_conflicts"
        )

        # ============================================================
        # 11. CRITIC INFORMATION
        # ============================================================

        critic_review = {
            "status": critic_result.status,
            "recommendation": critic_result.recommendation,
            "findings": [
                finding.model_dump()
                for finding in critic_result.findings
            ]
        }

        # ============================================================
        # 12. FINAL ROUTING RESULT
        # ============================================================

        routing = {
            "question_type": question_type,
            "business_area": business_area,
            "specialist_agents": specialist_names,
            "resolved_agents": resolved_agent_names,
            "unresolved_agents": unresolved_agents
        }

        # ============================================================
        # 13. FINAL RESULT
        # ============================================================

        return {
            "status": (
                "COMPLETED"
                if synthesis_result.status == "COMPLETED"
                else "FAILED"
            ),

            "routing": routing,

            "critic": critic_review,

            "answer": answer,

            "recommendation": recommendation,

            "confidence": confidence,

            "key_factors": (
                key_factors
                if isinstance(
                    key_factors,
                    list
                )
                else []
            ),

            "risks": (
                risks
                if isinstance(
                    risks,
                    list
                )
                else []
            ),

            "assumptions": (
                assumptions
                if isinstance(
                    assumptions,
                    list
                )
                else []
            ),

            "evidence": (
                evidence
                if isinstance(
                    evidence,
                    list
                )
                else []
            ),

            "agent_conflicts": (
                agent_conflicts
                if isinstance(
                    agent_conflicts,
                    list
                )
                else []
            ),

            "agents": context.agent_results
        }

    # ================================================================
    # ROUTING VALUE
    # ================================================================

    def _get_routing_value(
        self,
        router_result,
        factor_name: str
    ):

        for finding in router_result.findings:

            if finding.factor != factor_name:
                continue

            value = finding.value

            if isinstance(
                value,
                dict
            ):
                return value.get(
                    "value"
                )

            return value

        return None

    # ================================================================
    # ROUTING LIST
    # ================================================================

    def _get_routing_list(
        self,
        router_result,
        factor_name: str
    ) -> list[str]:

        for finding in router_result.findings:

            if finding.factor != factor_name:
                continue

            value = finding.value

            if not isinstance(
                value,
                list
            ):
                return []

            return [
                str(item)
                for item in value
            ]

        return []

    # ================================================================
    # AGENT FINDING
    # ================================================================

    def _get_agent_finding(
        self,
        agent_result,
        factor_name: str
    ):

        for finding in agent_result.findings:

            if finding.factor == factor_name:
                return finding.value

        return None

    # ================================================================
    # LEGACY CREDIT WORKFLOW
    # ================================================================

    def execute(
        self,
        data: dict[str, Any]
    ):

        context = DecisionContext(
            decision_id=data.get(
                "decision_id",
                "PENDING"
            ),
            input_data=data
        )

        # ============================================================
        # DATA
        # ============================================================

        data_result = self.data_agent.run(
            data
        )

        context.data_assessment = (
            data_result
        )

        context.add_agent_result(
            data_result
        )

        # ============================================================
        # RISK
        # ============================================================

        risk_result = self.risk_agent.run(
            data
        )

        context.risk_assessment = (
            risk_result
        )

        context.add_agent_result(
            risk_result
        )

        # ============================================================
        # FINANCE
        # ============================================================

        finance_result = (
            self.finance_agent.run(
                data
            )
        )

        context.finance_assessment = (
            finance_result
        )

        context.add_agent_result(
            finance_result
        )

        # ============================================================
        # GOVERNANCE
        # ============================================================

        governance_result = (
            self.governance_agent.run(
                data,
                context.agent_results
            )
        )

        context.add_agent_result(
            governance_result
        )

        # ============================================================
        # DECISION
        # ============================================================

        decision_input = {
            **data,
            "data_assessment": data_result,
            "risk_assessment": risk_result,
            "finance_assessment": finance_result,
            "governance_assessment": governance_result
        }

        final_result = (
            self.decision_agent.run(
                decision_input,
                context.agent_results
            )
        )

        context.final_decision = (
            final_result
        )

        # ============================================================
        # LEGACY CREDIT CRITIC
        # ============================================================

        critic_result = (
            self.critic_agent.run(
                data,
                context.agent_results
            )
        )

        context.add_agent_result(
            critic_result
        )

        # ============================================================
        # LEGACY CRITIC GATE
        # ============================================================

        if (
            critic_result.recommendation
            == "REVIEW"
        ):

            final_result["decision"] = (
                "MANUAL_REVIEW"
            )

            final_result["approved_limit"] = 0

            final_result["confidence"] = 0.0

            final_result["reasons"].insert(
                0,
                (
                    "Critic Agent identified an "
                    "inconsistency requiring manual review."
                )
            )

            final_result["conditions"] = [
                (
                    "Manual review is required because "
                    "the Critic Agent identified an issue."
                ),
                (
                    "Review conflicting agent assessments "
                    "before final approval."
                )
            ]

            explanation = (
                final_result["explanation"]
            )

            explanation.summary = (
                "The credit request requires manual review "
                "because the Critic Agent identified an "
                "inconsistency in the specialist assessments."
            )

            explanation.governance_status = (
                governance_result.status
            )

            explanation.governance_recommendation = (
                governance_result.recommendation
            )

            for finding in critic_result.findings:

                if (
                    finding.factor
                    == "agent_recommendation_conflict"
                ):

                    conflict = str(
                        finding.value
                    )

                    if (
                        conflict
                        not in explanation.agent_conflicts
                    ):
                        explanation.agent_conflicts.append(
                            conflict
                        )

        # ============================================================
        # LEGACY RESULT
        # ============================================================

        return {
            "decision": final_result[
                "decision"
            ],

            "approved_limit": final_result[
                "approved_limit"
            ],

            "confidence": final_result[
                "confidence"
            ],

            "reasons": final_result[
                "reasons"
            ],

            "conditions": final_result[
                "conditions"
            ],

            "explanation": final_result[
                "explanation"
            ],

            "ai_analysis": final_result[
                "ai_analysis"
            ],

            "agents": context.agent_results
        }