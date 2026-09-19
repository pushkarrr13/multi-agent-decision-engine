from .base_agent import BaseAgent
from ..schemas.decision_response import AgentResult, AgentFinding


class DataAgent(BaseAgent):

    name = "data_agent"

    def run(self, data: dict) -> AgentResult:

        required_fields = [
            "customer_id",
            "requested_credit_limit",
            "annual_revenue",
            "revenue_growth",
            "existing_debt",
            "payment_history_score",
            "credit_utilization",
            "customer_tenure_years",
            "industry_risk",
        ]

        missing_fields = [
            field for field in required_fields
            if data.get(field) is None
        ]

        if missing_fields:
            return AgentResult(
                agent_name=self.name,
                status="FAILED",
                recommendation="MANUAL_REVIEW",
                findings=[
                    AgentFinding(
                        factor="data_completeness",
                        value=missing_fields,
                        impact="negative",
                        reason="Required business information is missing."
                    )
                ]
            )

        return AgentResult(
            agent_name=self.name,
            status="COMPLETED",
            recommendation="DATA_VALID",
            findings=[
                AgentFinding(
                    factor="data_completeness",
                    value="100%",
                    impact="positive",
                    reason="All required decision fields are available."
                )
            ]
        )
