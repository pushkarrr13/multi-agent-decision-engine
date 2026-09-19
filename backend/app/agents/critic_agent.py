from typing import Any

from .base_agent import BaseAgent
from ..schemas.decision_response import AgentResult, AgentFinding


class CriticAgent(BaseAgent):
    """
    Legacy credit-decision Critic Agent.

    This agent is retained only for the old credit workflow.
    The generic business workflow uses GenericCriticAgent.
    """

    name = "critic_agent"

    def run(
        self,
        data: dict[str, Any],
        agent_results: list
    ):

        findings = []
        issues_found = False

        data_agent = None
        risk_agent = None
        finance_agent = None
        governance_agent = None

        # ============================================================
        # FIND REQUIRED CREDIT AGENTS
        # ============================================================

        for agent in agent_results:

            if agent.agent_name == "data_agent":
                data_agent = agent

            elif agent.agent_name == "risk_agent":
                risk_agent = agent

            elif agent.agent_name == "finance_agent":
                finance_agent = agent

            elif agent.agent_name == "governance_agent":
                governance_agent = agent

        # ============================================================
        # DATA AGENT CHECK
        # ============================================================

        if data_agent is None:

            issues_found = True

            findings.append(
                AgentFinding(
                    factor="data_agent_result",
                    value="missing",
                    impact="negative",
                    reason=(
                        "Critic could not find a "
                        "Data Agent result."
                    )
                )
            )

        elif data_agent.status != "COMPLETED":

            issues_found = True

            findings.append(
                AgentFinding(
                    factor="data_quality",
                    value=data_agent.status,
                    impact="negative",
                    reason=(
                        "Data Agent did not complete "
                        "successfully."
                    )
                )
            )

        else:

            findings.append(
                AgentFinding(
                    factor="data_quality",
                    value="valid",
                    impact="positive",
                    reason=(
                        "Data Agent completed successfully."
                    )
                )
            )

        # ============================================================
        # RISK AGENT CHECK
        # ============================================================

        if risk_agent is None:

            issues_found = True

            findings.append(
                AgentFinding(
                    factor="risk_agent_result",
                    value="missing",
                    impact="negative",
                    reason=(
                        "Critic could not find a "
                        "Risk Agent result."
                    )
                )
            )

        elif risk_agent.score is None:

            issues_found = True

            findings.append(
                AgentFinding(
                    factor="risk_score",
                    value=None,
                    impact="negative",
                    reason=(
                        "Risk Agent completed without "
                        "providing a score."
                    )
                )
            )

        else:

            findings.append(
                AgentFinding(
                    factor="risk_score",
                    value=risk_agent.score,
                    impact="positive",
                    reason=(
                        "Risk Agent provided a valid score."
                    )
                )
            )

        # ============================================================
        # FINANCE AGENT CHECK
        # ============================================================

        if finance_agent is None:

            issues_found = True

            findings.append(
                AgentFinding(
                    factor="finance_agent_result",
                    value="missing",
                    impact="negative",
                    reason=(
                        "Critic could not find a "
                        "Finance Agent result."
                    )
                )
            )

        elif finance_agent.score is None:

            issues_found = True

            findings.append(
                AgentFinding(
                    factor="finance_score",
                    value=None,
                    impact="negative",
                    reason=(
                        "Finance Agent completed without "
                        "providing a score."
                    )
                )
            )

        else:

            findings.append(
                AgentFinding(
                    factor="finance_score",
                    value=finance_agent.score,
                    impact="positive",
                    reason=(
                        "Finance Agent provided a valid score."
                    )
                )
            )

        # ============================================================
        # GOVERNANCE CHECK
        # ============================================================

        if governance_agent is None:

            issues_found = True

            findings.append(
                AgentFinding(
                    factor="governance_result",
                    value="missing",
                    impact="negative",
                    reason=(
                        "Governance Agent result was "
                        "not available."
                    )
                )
            )

        elif (
            governance_agent.recommendation
            == "MANUAL_REVIEW"
        ):

            issues_found = True

            findings.append(
                AgentFinding(
                    factor="governance_review",
                    value="MANUAL_REVIEW",
                    impact="negative",
                    reason=(
                        "Governance Agent requires "
                        "manual review."
                    )
                )
            )

        else:

            findings.append(
                AgentFinding(
                    factor="governance_review",
                    value="PROCEED",
                    impact="positive",
                    reason=(
                        "Governance checks allow the "
                        "process to proceed."
                    )
                )
            )

        # ============================================================
        # RISK / FINANCE RECOMMENDATION CONFLICT
        # ============================================================

        if (
            risk_agent is not None
            and finance_agent is not None
        ):

            if (
                risk_agent.recommendation
                != finance_agent.recommendation
            ):

                issues_found = True

                findings.append(
                    AgentFinding(
                        factor="agent_recommendation_conflict",
                        value=(
                            f"Risk={risk_agent.recommendation}, "
                            f"Finance={finance_agent.recommendation}"
                        ),
                        impact="negative",
                        reason=(
                            "Risk and Finance Agents "
                            "produced different recommendations."
                        )
                    )
                )

            else:

                findings.append(
                    AgentFinding(
                        factor="agent_recommendation_consistency",
                        value=(
                            risk_agent.recommendation
                        ),
                        impact="positive",
                        reason=(
                            "Risk and Finance Agents "
                            "have consistent recommendations."
                        )
                    )
                )

        # ============================================================
        # REQUESTED CREDIT LIMIT RATIO
        # ============================================================

        requested_limit = data.get(
            "requested_credit_limit"
        )

        annual_revenue = data.get(
            "annual_revenue"
        )

        if (
            requested_limit is not None
            and annual_revenue is not None
            and annual_revenue > 0
        ):

            requested_ratio = (
                requested_limit
                / annual_revenue
            )

            if requested_ratio > 0.50:

                issues_found = True

                findings.append(
                    AgentFinding(
                        factor="requested_limit_ratio",
                        value=round(
                            requested_ratio,
                            3
                        ),
                        impact="negative",
                        reason=(
                            "Requested credit limit is "
                            "greater than 50% of annual revenue."
                        )
                    )
                )

            else:

                findings.append(
                    AgentFinding(
                        factor="requested_limit_ratio",
                        value=round(
                            requested_ratio,
                            3
                        ),
                        impact="positive",
                        reason=(
                            "Requested credit limit is "
                            "within the critic's configured threshold."
                        )
                    )
                )

        # ============================================================
        # FINAL RECOMMENDATION
        # ============================================================

        recommendation = (
            "REVIEW"
            if issues_found
            else "PASS"
        )

        return AgentResult(
            agent_name=self.name,
            status="COMPLETED",
            score=None,
            recommendation=recommendation,
            findings=findings
        )