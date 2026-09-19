from typing import Any

from .base_agent import BaseAgent
from ..services.llm_service import LLMService
from ..schemas.decision_response import (
    DecisionExplanation,
    RuleResult
)


class DecisionAgent(BaseAgent):

    name = "decision_agent"

    def __init__(self):

        self.llm_service = LLMService()

    def run(
        self,
        data: dict[str, Any],
        agent_results: list
    ):

        risk_score = 0.0
        finance_score = 0.0

        risk_agent = None
        finance_agent = None
        governance_agent = None

        # -------------------------------------------------
        # Collect Agent Results
        # -------------------------------------------------

        for agent in agent_results:

            if agent.agent_name == "risk_agent":

                risk_agent = agent
                risk_score = agent.score or 0.0

            elif agent.agent_name == "finance_agent":

                finance_agent = agent
                finance_score = agent.score or 0.0

            elif agent.agent_name == "governance_agent":

                governance_agent = agent

        # -------------------------------------------------
        # Governance Check
        # -------------------------------------------------

        governance_decision = "PASS"
        governance_status = "UNKNOWN"
        governance_recommendation = "UNKNOWN"

        if governance_agent is not None:

            governance_status = (
                governance_agent.status
            )

            governance_recommendation = (
                governance_agent.recommendation
            )

            if governance_agent.status != "COMPLETED":

                governance_decision = "BLOCK"

            elif (
                governance_agent.recommendation
                == "MANUAL_REVIEW"
            ):

                governance_decision = "BLOCK"

        # -------------------------------------------------
        # Calculate Combined Decision Score
        # -------------------------------------------------

        combined_score = (
            risk_score * 0.60
            + finance_score * 0.40
        )

        combined_score = round(
            combined_score,
            2
        )

        # -------------------------------------------------
        # Determine Initial Decision
        # -------------------------------------------------

        if governance_decision == "BLOCK":

            decision = "MANUAL_REVIEW"

            approved_limit = 0

            confidence = 0.0

        else:

            if combined_score >= 75:

                decision = "APPROVE"

            elif combined_score >= 60:

                decision = (
                    "APPROVE_WITH_CONDITIONS"
                )

            else:

                decision = "REJECT"

            if decision == "APPROVE":

                approved_limit = data[
                    "requested_credit_limit"
                ]

            elif (
                decision
                == "APPROVE_WITH_CONDITIONS"
            ):

                approved_limit = (
                    data[
                        "requested_credit_limit"
                    ]
                    * 0.75
                )

            else:

                approved_limit = 0

            confidence = round(
                combined_score / 100,
                2
            )

        # -------------------------------------------------
        # Extract Findings
        # -------------------------------------------------

        positive_factors = []

        risk_factors = []

        if risk_agent is not None:

            for finding in risk_agent.findings:

                if finding.impact == "positive":

                    positive_factors.append(
                        finding.reason
                    )

                elif finding.impact == "negative":

                    risk_factors.append(
                        finding.reason
                    )

        if finance_agent is not None:

            for finding in finance_agent.findings:

                if finding.impact == "positive":

                    positive_factors.append(
                        finding.reason
                    )

                elif finding.impact == "negative":

                    risk_factors.append(
                        finding.reason
                    )

        # -------------------------------------------------
        # Extract Triggered Business Rules
        # -------------------------------------------------

        triggered_rules = []

        if governance_agent is not None:

            for finding in governance_agent.findings:

                if not finding.factor.startswith(
                    "business_rule:"
                ):

                    continue

                if not isinstance(
                    finding.value,
                    dict
                ):

                    continue

                rule_id = finding.factor.split(
                    ":",
                    1
                )[1]

                if (
                    finding.value.get(
                        "action"
                    )
                    == "MANUAL_REVIEW"
                ):

                    triggered_rules.append(
                        RuleResult(
                            rule_id=rule_id,
                            rule_name=(
                                finding.value.get(
                                    "rule_name",
                                    rule_id
                                )
                            ),
                            description=(
                                finding.reason
                            ),
                            severity=(
                                finding.value.get(
                                    "severity",
                                    "UNKNOWN"
                                )
                            ),
                            action=(
                                finding.value.get(
                                    "action",
                                    "MANUAL_REVIEW"
                                )
                            ),
                            triggered=True
                        )
                    )

        # -------------------------------------------------
        # Extract Agent Conflicts
        # -------------------------------------------------

        agent_conflicts = []

        if (
            risk_agent is not None
            and finance_agent is not None
        ):

            if (
                risk_agent.recommendation
                != finance_agent.recommendation
            ):

                agent_conflicts.append(
                    (
                        "Risk Agent recommendation "
                        f"is {risk_agent.recommendation}, "
                        "while Finance Agent recommendation "
                        f"is {finance_agent.recommendation}."
                    )
                )

        # -------------------------------------------------
        # Explanation Summary
        # -------------------------------------------------

        if decision == "APPROVE":

            summary = (
                "The credit request passed "
                "specialist agent assessments and "
                "governance validation."
            )

        elif decision == "APPROVE_WITH_CONDITIONS":

            summary = (
                "The credit request met the "
                "decision threshold but requires "
                "conditional approval."
            )

        elif decision == "REJECT":

            summary = (
                "The credit request did not meet "
                "the configured decision threshold."
            )

        else:

            summary = (
                "The credit request requires "
                "manual review because governance "
                "validation or business rules "
                "prevented automatic approval."
            )

        # -------------------------------------------------
        # Build Structured Explanation
        # -------------------------------------------------

        explanation = DecisionExplanation(

            summary=summary,

            key_positive_factors=(
                positive_factors
            ),

            key_risk_factors=(
                risk_factors
            ),

            triggered_rules=(
                triggered_rules
            ),

            agent_conflicts=(
                agent_conflicts
            ),

            governance_status=(
                governance_status
            ),

            governance_recommendation=(
                governance_recommendation
            ),

            decision_score=(
                combined_score
            ),

            risk_score=(
                risk_score
            ),

            finance_score=(
                finance_score
            )
        )

        # -------------------------------------------------
        # Reasons
        # -------------------------------------------------

        reasons = []

        if governance_decision == "BLOCK":

            reasons.append(
                "Governance validation blocked "
                "automatic approval."
            )

        if triggered_rules:

            reasons.append(
                f"{len(triggered_rules)} "
                "business rule(s) require "
                "manual review."
            )

        if agent_conflicts:

            reasons.append(
                "Risk and Finance Agents "
                "produced conflicting "
                "recommendations."
            )

        reasons.extend(
            [
                (
                    "Risk assessment score: "
                    f"{risk_score}/100"
                ),
                (
                    "Financial assessment score: "
                    f"{finance_score}/100"
                ),
                (
                    "Combined decision score: "
                    f"{combined_score}/100"
                )
            ]
        )

        # -------------------------------------------------
        # Conditions
        # -------------------------------------------------

        conditions = []

        if decision == "APPROVE_WITH_CONDITIONS":

            conditions.append(
                "Approved limit is restricted "
                "to 75% of the requested amount."
            )

        if governance_decision == "BLOCK":

            conditions.append(
                "Manual review is required "
                "before credit approval."
            )

        if triggered_rules:

            conditions.append(
                "Review all triggered business "
                "rules before final approval."
            )

        if agent_conflicts:

            conditions.append(
                "Review conflicting specialist "
                "agent recommendations."
            )

        # -------------------------------------------------
        # AI Analysis
        # -------------------------------------------------

        ai_analysis = (
            self.llm_service.analyze_decision(
                customer_data=data,
                agent_results=agent_results
            )
        )

        # -------------------------------------------------
        # Final Result
        # -------------------------------------------------

        return {
            "decision": decision,

            "approved_limit": (
                approved_limit
            ),

            "confidence": confidence,

            "reasons": reasons,

            "conditions": conditions,

            "explanation": explanation,

            "ai_analysis": ai_analysis
        }