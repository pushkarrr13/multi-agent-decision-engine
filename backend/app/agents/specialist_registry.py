from typing import Any

from .specialist_agent import SpecialistAgent


class SpecialistRegistry:
    """
    Central registry for dynamically selected specialist agents.

    The Question Router returns agent names.
    The registry converts those names into actual agent instances.
    """

    def __init__(self):
        self._agents = {
            "finance_agent": SpecialistAgent(
                specialist_name="finance_agent",
                domain="Finance"
            ),

            "sales_agent": SpecialistAgent(
                specialist_name="sales_agent",
                domain="Sales"
            ),

            "marketing_agent": SpecialistAgent(
                specialist_name="marketing_agent",
                domain="Marketing"
            ),

            "customer_agent": SpecialistAgent(
                specialist_name="customer_agent",
                domain="Customer"
            ),

            "operations_agent": SpecialistAgent(
                specialist_name="operations_agent",
                domain="Operations"
            ),

            "product_agent": SpecialistAgent(
                specialist_name="product_agent",
                domain="Product"
            ),

            "hr_agent": SpecialistAgent(
                specialist_name="hr_agent",
                domain="Human Resources"
            ),

            "procurement_agent": SpecialistAgent(
                specialist_name="procurement_agent",
                domain="Procurement"
            ),

            "strategy_agent": SpecialistAgent(
                specialist_name="strategy_agent",
                domain="Strategy"
            ),

            "risk_agent": SpecialistAgent(
                specialist_name="risk_agent",
                domain="Risk"
            ),

            "technology_agent": SpecialistAgent(
                specialist_name="technology_agent",
                domain="Technology"
            ),

            "compliance_agent": SpecialistAgent(
                specialist_name="compliance_agent",
                domain="Compliance"
            ),

            "market_agent": SpecialistAgent(
                specialist_name="market_agent",
                domain="Market"
            ),
        }

    def get(
        self,
        agent_name: str
    ) -> SpecialistAgent | None:

        return self._agents.get(agent_name)

    def get_many(
        self,
        agent_names: list[str]
    ) -> list[SpecialistAgent]:

        agents = []

        for agent_name in agent_names:
            agent = self.get(agent_name)

            if agent is not None:
                agents.append(agent)

        return agents

    def available_agents(self) -> list[str]:
        return list(self._agents.keys())