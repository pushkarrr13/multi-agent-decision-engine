from typing import Any

from .rules import BUSINESS_RULES


class RuleEngine:

    def __init__(self):

        self.rules = BUSINESS_RULES

    def evaluate(
        self,
        data: dict[str, Any]
    ) -> dict[str, Any]:

        triggered_rules = []
        passed_rules = []

        for rule in self.rules:

            try:

                triggered = rule.check(data)

            except Exception as e:

                triggered_rules.append(
                    {
                        "rule_id": rule.rule_id,
                        "rule_name": rule.name,
                        "description": rule.description,
                        "severity": "CRITICAL",
                        "action": "MANUAL_REVIEW",
                        "triggered": True,
                        "error": str(e)
                    }
                )

                continue

            rule_result = {
                "rule_id": rule.rule_id,
                "rule_name": rule.name,
                "description": rule.description,
                "severity": rule.severity,
                "action": rule.action,
                "triggered": triggered
            }

            if triggered:

                triggered_rules.append(
                    rule_result
                )

            else:

                passed_rules.append(
                    rule_result
                )

        requires_manual_review = any(
            rule["action"] == "MANUAL_REVIEW"
            for rule in triggered_rules
        )

        critical_rules_triggered = any(
            rule["severity"] == "CRITICAL"
            for rule in triggered_rules
        )

        return {
            "total_rules": len(self.rules),

            "rules_evaluated": (
                len(triggered_rules)
                + len(passed_rules)
            ),

            "triggered_rules": triggered_rules,

            "passed_rules": passed_rules,

            "triggered_rule_count": (
                len(triggered_rules)
            ),

            "passed_rule_count": (
                len(passed_rules)
            ),

            "requires_manual_review": (
                requires_manual_review
            ),

            "critical_rules_triggered": (
                critical_rules_triggered
            ),

            "overall_status": (
                "REVIEW"
                if requires_manual_review
                else "PASS"
            )
        }