from .base_agent import BaseAgent
from ..schemas.decision_response import AgentResult, AgentFinding


class RiskAgent(BaseAgent):

    name = "risk_agent"

    def run(self, data: dict) -> AgentResult:

        score = 50
        findings = []

        payment_score = data["payment_history_score"]

        if payment_score >= 90:
            score += 20
            findings.append(
                AgentFinding(
                    factor="payment_history",
                    value=payment_score,
                    impact="positive",
                    reason="Strong payment history."
                )
            )
        elif payment_score >= 75:
            score += 10
            findings.append(
                AgentFinding(
                    factor="payment_history",
                    value=payment_score,
                    impact="positive",
                    reason="Acceptable payment history."
                )
            )
        else:
            score -= 20
            findings.append(
                AgentFinding(
                    factor="payment_history",
                    value=payment_score,
                    impact="negative",
                    reason="Weak payment history."
                )
            )

        growth = data["revenue_growth"]

        if growth >= 15:
            score += 15
            findings.append(
                AgentFinding(
                    factor="revenue_growth",
                    value=growth,
                    impact="positive",
                    reason="Strong positive revenue growth."
                )
            )
        elif growth < 0:
            score -= 15
            findings.append(
                AgentFinding(
                    factor="revenue_growth",
                    value=growth,
                    impact="negative",
                    reason="Business revenue is declining."
                )
            )

        utilization = data["credit_utilization"]

        if utilization > 50:
            score -= 15
            findings.append(
                AgentFinding(
                    factor="credit_utilization",
                    value=utilization,
                    impact="negative",
                    reason="High credit utilization."
                )
            )
        elif utilization > 30:
            score -= 8
            findings.append(
                AgentFinding(
                    factor="credit_utilization",
                    value=utilization,
                    impact="negative",
                    reason="Moderately high credit utilization."
                )
            )

        industry_risk = data["industry_risk"].upper()

        if industry_risk == "HIGH":
            score -= 15
        elif industry_risk == "LOW":
            score += 5

        score = max(0, min(100, score))

        if score >= 75:
            recommendation = "APPROVE"
        elif score >= 60:
            recommendation = "APPROVE_WITH_CONDITIONS"
        else:
            recommendation = "MANUAL_REVIEW"

        return AgentResult(
            agent_name=self.name,
            status="COMPLETED",
            score=score,
            recommendation=recommendation,
            findings=findings
        )
