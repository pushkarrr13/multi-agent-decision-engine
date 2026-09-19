from typing import Any

from .base_agent import BaseAgent
from ..schemas.decision_response import (
    AgentResult,
    AgentFinding
)
from ..rules.rule_engine import RuleEngine


class GovernanceAgent(BaseAgent):

    name = "governance_agent"

    def __init__(self):

        self.rule_engine = RuleEngine()

    def run(
        self,
        data: dict[str, Any],
        agent_results: list
    ):

        findings = []

        governance_decision = "PASS"
        recommendation = "PROCEED"

        data_agent = None
        risk_agent = None
        finance_agent = None

        for agent in agent_results:

            if agent.agent_name == "data_agent":

                data_agent = agent

            elif agent.agent_name == "risk_agent":

                risk_agent = agent

            elif agent.agent_name == "finance_agent":

                finance_agent = agent

        # -------------------------------------------------
        # 1. Run Business Rules
        # -------------------------------------------------

        rule_result = self.rule_engine.evaluate(data)

        # -------------------------------------------------
        # 2. Data Agent Validation
        # -------------------------------------------------

        if data_agent is None:

            governance_decision = "BLOCK"

            findings.append(
                AgentFinding(
                    factor="data_agent_availability",
                    value="missing",
                    impact="negative",
                    reason=(
                        "Data Agent result was not available."
                    )
                )
            )

        elif data_agent.status != "COMPLETED":

            governance_decision = "BLOCK"

            findings.append(
                AgentFinding(
                    factor="data_quality",
                    value=data_agent.status,
                    impact="negative",
                    reason=(
                        "Data validation did not complete "
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
                        "Required decision data passed "
                        "validation."
                    )
                )
            )

        # -------------------------------------------------
        # 3. Risk Agent Availability
        # -------------------------------------------------

        if risk_agent is None:

            governance_decision = "BLOCK"

            findings.append(
                AgentFinding(
                    factor="risk_agent_availability",
                    value="missing",
                    impact="negative",
                    reason=(
                        "Risk Agent result was not available."
                    )
                )
            )

        # -------------------------------------------------
        # 4. Finance Agent Availability
        # -------------------------------------------------

        if finance_agent is None:

            governance_decision = "BLOCK"

            findings.append(
                AgentFinding(
                    factor="finance_agent_availability",
                    value="missing",
                    impact="negative",
                    reason=(
                        "Finance Agent result was not available."
                    )
                )
            )

        # -------------------------------------------------
        # 5. Business Rule Results
        # -------------------------------------------------

        triggered_rules = rule_result[
            "triggered_rules"
        ]

        passed_rules = rule_result[
            "passed_rules"
        ]

        for rule in triggered_rules:

            impact = "negative"

            findings.append(
                AgentFinding(
                    factor=(
                        f"business_rule:{rule['rule_id']}"
                    ),
                    value={
                        "rule_name": rule["rule_name"],
                        "severity": rule["severity"],
                        "action": rule["action"]
                    },
                    impact=impact,
                    reason=rule["description"]
                )
            )

        for rule in passed_rules:

            findings.append(
                AgentFinding(
                    factor=(
                        f"business_rule:{rule['rule_id']}"
                    ),
                    value="passed",
                    impact="positive",
                    reason=(
                        f"Business rule "
                        f"{rule['rule_name']} "
                        f"was satisfied."
                    )
                )
            )

        # -------------------------------------------------
        # 6. Business Rule Governance Decision
        # -------------------------------------------------

        if rule_result[
            "requires_manual_review"
        ]:

            governance_decision = "BLOCK"

            findings.append(
                AgentFinding(
                    factor="business_rules",
                    value={
                        "status": rule_result[
                            "overall_status"
                        ],
                        "triggered_rule_count": (
                            rule_result[
                                "triggered_rule_count"
                            ]
                        ),
                        "critical_rules_triggered": (
                            rule_result[
                                "critical_rules_triggered"
                            ]
                        )
                    },
                    impact="negative",
                    reason=(
                        "One or more business rules "
                        "require manual review."
                    )
                )
            )

        else:

            findings.append(
                AgentFinding(
                    factor="business_rules",
                    value={
                        "status": "PASS",
                        "triggered_rule_count": 0
                    },
                    impact="positive",
                    reason=(
                        "All configured business rules "
                        "passed successfully."
                    )
                )
            )

        # -------------------------------------------------
        # 7. Final Governance Status
        # -------------------------------------------------

        if governance_decision == "BLOCK":

            recommendation = "MANUAL_REVIEW"

            status = "FAILED"

        else:

            recommendation = "PROCEED"

            status = "COMPLETED"

        # -------------------------------------------------
        # 8. Return Governance Result
        # -------------------------------------------------

        return AgentResult(
            agent_name=self.name,
            status=status,
            score=None,
            recommendation=recommendation,
            findings=findings
        )