from typing import Any


class DecisionContext:

    def __init__(self, decision_id: str, input_data: dict[str, Any]):
        self.decision_id = decision_id
        self.input_data = input_data

        self.data_assessment = None
        self.risk_assessment = None
        self.finance_assessment = None

        self.agent_results = []

        self.final_decision = None

    def add_agent_result(self, result):
        self.agent_results.append(result)

    def to_dict(self):
        return {
            "decision_id": self.decision_id,
            "input_data": self.input_data,
            "data_assessment": self.data_assessment,
            "risk_assessment": self.risk_assessment,
            "finance_assessment": self.finance_assessment,
            "agent_results": self.agent_results,
            "final_decision": self.final_decision
        }
