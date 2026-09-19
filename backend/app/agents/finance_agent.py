from .base_agent import BaseAgent
from ..schemas.decision_response import AgentResult, AgentFinding


class FinanceAgent(BaseAgent):

    name = "finance_agent"

    def run(self, data: dict) -> AgentResult:

        revenue = data["annual_revenue"]
        debt = data["existing_debt"]
        requested_limit = data["requested_credit_limit"]

        findings = []

        debt_ratio = debt / revenue

        if debt_ratio < 0.30:
            financial_score = 90
            impact = "positive"
            reason = "Debt exposure is relatively low."

        elif debt_ratio < 0.50:
            financial_score = 70
            impact = "neutral"
            reason = "Debt exposure is moderate."

        else:
            financial_score = 45
            impact = "negative"
            reason = "Debt exposure is relatively high."

        findings.append(
            AgentFinding(
                factor="debt_to_revenue",
                value=round(debt_ratio, 3),
                impact=impact,
                reason=reason
            )
        )

        limit_ratio = requested_limit / revenue

        findings.append(
            AgentFinding(
                factor="requested_limit_to_revenue",
                value=round(limit_ratio, 3),
                impact="neutral",
                reason="Requested credit limit evaluated against annual revenue."
            )
        )

        if financial_score >= 75:
            recommendation = "APPROVE"
        elif financial_score >= 60:
            recommendation = "APPROVE_WITH_CONDITIONS"
        else:
            recommendation = "MANUAL_REVIEW"

        return AgentResult(
            agent_name=self.name,
            status="COMPLETED",
            score=financial_score,
            recommendation=recommendation,
            findings=findings
        )
