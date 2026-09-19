import json

from google import genai

from ..config import settings


class LLMService:
    """
    Central Gemini service for the Multi-Agent Business Decision Engine.

    Supported capabilities:

    1. Generic business-question routing
    2. Generic specialist synthesis
    3. Generic critic analysis
    4. Legacy credit-decision explanation
    """

    def __init__(self):
        if not settings.gemini_api_key:
            raise RuntimeError(
                "GEMINI_API_KEY is not configured"
            )

        self.client = genai.Client(
            api_key=settings.gemini_api_key
        )

        self.model = settings.gemini_model

    # ============================================================
    # GENERIC BUSINESS QUESTION ROUTING
    # ============================================================

    def route_business_question(
        self,
        question: str,
        question_type: str = "AUTO",
        business_area: str = "AUTO",
        context: dict | None = None,
        objectives: list | None = None,
        constraints: list | None = None,
    ) -> dict:

        context = context or {}
        objectives = objectives or []
        constraints = constraints or []

        available_agents = [
            "finance_agent",
            "sales_agent",
            "marketing_agent",
            "customer_agent",
            "operations_agent",
            "product_agent",
            "hr_agent",
            "procurement_agent",
            "strategy_agent",
            "risk_agent",
            "technology_agent",
            "compliance_agent",
            "market_agent",
        ]

        prompt = f"""
You are the Question Router for a generic multi-agent
business decision engine.

Your job is to understand the business question semantically
and determine:

1. What type of business question it is.
2. What business area it belongs to.
3. Which specialist agents should analyze it.

The platform is NOT limited to credit or finance.

Possible question types:

ANALYZE
COMPARE
INVESTIGATE
PREDICT
RECOMMEND
DECIDE
EXPLAIN
OPTIMIZE

Possible business areas:

FINANCE
SALES
MARKETING
CUSTOMER
OPERATIONS
PRODUCT
HR
PROCUREMENT
STRATEGY
RISK
TECHNOLOGY
COMPLIANCE
MARKET
GENERAL

Available specialist agents:

{available_agents}

USER QUESTION:
{question}

USER QUESTION TYPE:
{question_type}

USER BUSINESS AREA:
{business_area}

BUSINESS CONTEXT:
{context}

OBJECTIVES:
{objectives}

CONSTRAINTS:
{constraints}

ROUTING RULES:

- Understand the meaning of the question, not only keywords.
- Select every specialist that can materially contribute.
- Do not select unrelated specialists.
- Prefer the minimum useful set of specialists.
- Do not invent business facts.
- Do not calculate scores.
- Respect supplied question type unless invalid.
- Respect supplied business area unless invalid.
- Evidence and Critic are core platform agents and are handled
  separately. Do not include them in specialist_agents.

Return ONLY valid JSON.

Required structure:

{{
    "question_type": "ANALYZE",
    "business_area": "FINANCE",
    "specialist_agents": [
        "finance_agent"
    ],
    "reasoning": "Brief explanation of why these agents were selected."
}}
"""

        try:
            interaction = self.client.interactions.create(
                model=self.model,
                input=prompt
            )

            output_text = (
                interaction.output_text
                if interaction.output_text
                else ""
            ).strip()

            if not output_text:
                raise ValueError(
                    "Gemini returned an empty routing response."
                )

            parsed = self._parse_json_response(
                output_text
            )

            return self._validate_routing_result(
                parsed,
                available_agents
            )

        except Exception as e:
            raise RuntimeError(
                f"Gemini business-question routing failed: {str(e)}"
            ) from e

    # ============================================================
    # GENERIC BUSINESS QUESTION CRITIQUE
    # ============================================================

    def critique_business_question(
        self,
        question: str,
        question_type: str,
        business_area: str,
        context: dict | None,
        objectives: list | None,
        constraints: list | None,
        agent_results: list
    ) -> dict:
        """
        Review evidence and specialist outputs before synthesis.

        Gemini determines whether differences between agents are:

        - TRUE_CONFLICT
        - COMPLEMENTARY
        - INSUFFICIENT_EVIDENCE

        It also identifies reasoning gaps and evidence problems.
        """

        context = context or {}
        objectives = objectives or []
        constraints = constraints or []

        prompt = f"""
You are the Critic Agent in a generic multi-agent
business decision engine.

Your responsibility is to critically review the outputs
of the Evidence Agent and specialist agents BEFORE the
final Synthesis Agent produces an answer.

BUSINESS QUESTION:
{question}

QUESTION TYPE:
{question_type}

BUSINESS AREA:
{business_area}

BUSINESS CONTEXT:
{context}

OBJECTIVES:
{objectives}

CONSTRAINTS:
{constraints}

AGENT RESULTS:
{agent_results}

IMPORTANT:

- Do not invent facts.
- Do not create missing evidence.
- Do not automatically treat different recommendations
  as contradictions.
- Two agents may have complementary recommendations.
- A TRUE_CONFLICT exists only when agents make materially
  incompatible claims or recommendations about the same issue.
- Identify evidence gaps that prevent reliable conclusions.
- Identify reasoning problems.
- Preserve specialist differences when they are complementary.
- Review the evidence before judging the conclusions.
- Do not make the final business decision.

CLASSIFICATION:

TRUE_CONFLICT:
Agents materially disagree about the same issue.

COMPLEMENTARY:
Agents provide different but compatible perspectives.

INSUFFICIENT_EVIDENCE:
The available information does not support a reliable
conclusion.

PASS:
No material analytical problem was identified.

Return ONLY valid JSON.

Required structure:

{{
    "status": "PASS",
    "overall_assessment": "Brief critical assessment.",
    "conflicts": [
        {{
            "type": "TRUE_CONFLICT",
            "agents": [
                "agent_a",
                "agent_b"
            ],
            "description": "Explain the disagreement.",
            "material": true
        }}
    ],
    "complementary_findings": [
        {{
            "agents": [
                "agent_a",
                "agent_b"
            ],
            "description": "Explain why the findings are complementary."
        }}
    ],
    "evidence_gaps": [
        "Missing evidence that limits the analysis."
    ],
    "reasoning_issues": [
        "Reasoning problem identified in the agent outputs."
    ],
    "confidence": 0.0
}}

STATUS RULES:

PASS:
No material issue exists.

REVIEW:
A material conflict, major evidence gap, or significant
reasoning problem exists.

CONFIDENCE:

Use a number between 0 and 1.

Confidence represents how strongly the critic's assessment
is supported by the supplied agent outputs.
It is not a statistical probability.
"""

        try:
            interaction = self.client.interactions.create(
                model=self.model,
                input=prompt
            )

            output_text = (
                interaction.output_text
                if interaction.output_text
                else ""
            ).strip()

            if not output_text:
                raise ValueError(
                    "Gemini returned an empty critic response."
                )

            parsed = self._parse_json_response(
                output_text
            )

            return self._validate_critique_result(
                parsed
            )

        except Exception as e:
            raise RuntimeError(
                f"Gemini business-question critique failed: {str(e)}"
            ) from e

    # ============================================================
    # GENERIC BUSINESS QUESTION SYNTHESIS
    # ============================================================

    def synthesize_business_question(
        self,
        question: str,
        question_type: str,
        business_area: str,
        context: dict | None,
        objectives: list | None,
        constraints: list | None,
        agent_results: list
    ) -> dict:

        context = context or {}
        objectives = objectives or []
        constraints = constraints or []

        prompt = f"""
You are the Synthesis Agent of a generic multi-agent
business decision engine.

Your responsibility is to combine the supplied business
question, context, objectives, constraints, specialist
findings and critic findings into one useful and auditable
business response.

IMPORTANT:

- This is a generic business engine.
- Do not assume the question is about credit.
- Do not invent facts or data.
- Do not create numerical values that are not present.
- Clearly identify assumptions and missing evidence.
- Distinguish observed facts from interpretation.
- Preserve meaningful specialist differences.
- Treat Critic findings as validation evidence.
- Do not treat complementary agent viewpoints as conflicts.
- When a true conflict exists, explain it.
- Do not claim certainty when evidence is incomplete.
- A recommendation is allowed only when the evidence supports it.

BUSINESS QUESTION:
{question}

QUESTION TYPE:
{question_type}

BUSINESS AREA:
{business_area}

BUSINESS CONTEXT:
{context}

OBJECTIVES:
{objectives}

CONSTRAINTS:
{constraints}

AGENT RESULTS:
{agent_results}

Return ONLY valid JSON.

Required structure:

{{
    "answer": "Clear answer to the business question.",
    "recommendation": "Recommended action or null when not justified.",
    "confidence": 0.0,
    "key_factors": [
        "Important factor 1",
        "Important factor 2"
    ],
    "risks": [
        "Important risk 1"
    ],
    "assumptions": [
        "Important assumption or missing information"
    ],
    "evidence": [
        {{
            "source": "agent_name",
            "factor": "factor name",
            "value": "observed value",
            "reason": "why this evidence matters"
        }}
    ],
    "agent_conflicts": [
        "Description of a true specialist conflict"
    ]
}}

CONFIDENCE RULES:

- confidence must be between 0 and 1.
- Confidence is not a statistical probability.
- Do not assign high confidence when evidence is incomplete.
- Do not classify complementary viewpoints as conflicts.
"""

        try:
            interaction = self.client.interactions.create(
                model=self.model,
                input=prompt
            )

            output_text = (
                interaction.output_text
                if interaction.output_text
                else ""
            ).strip()

            if not output_text:
                raise ValueError(
                    "Gemini returned an empty synthesis response."
                )

            parsed = self._parse_json_response(
                output_text
            )

            return self._validate_synthesis_result(
                parsed
            )

        except Exception as e:
            raise RuntimeError(
                f"Gemini business-question synthesis failed: {str(e)}"
            ) from e

    # ============================================================
    # JSON PARSING
    # ============================================================

    def _parse_json_response(
        self,
        output_text: str
    ) -> dict:

        cleaned = output_text.strip()

        if cleaned.startswith("```"):

            lines = cleaned.splitlines()

            if lines:
                lines = lines[1:]

            if (
                lines
                and lines[-1].strip() == "```"
            ):
                lines = lines[:-1]

            cleaned = "\n".join(
                lines
            ).strip()

        parsed = json.loads(
            cleaned
        )

        if not isinstance(
            parsed,
            dict
        ):
            raise ValueError(
                "Gemini response must be a JSON object."
            )

        return parsed

    # ============================================================
    # ROUTING VALIDATION
    # ============================================================

    def _validate_routing_result(
        self,
        result: dict,
        available_agents: list[str]
    ) -> dict:

        question_type = str(
            result.get(
                "question_type",
                "ANALYZE"
            )
        ).upper()

        business_area = str(
            result.get(
                "business_area",
                "GENERAL"
            )
        ).upper()

        specialist_agents = result.get(
            "specialist_agents",
            []
        )

        reasoning = str(
            result.get(
                "reasoning",
                ""
            )
        ).strip()

        valid_question_types = {
            "ANALYZE",
            "COMPARE",
            "INVESTIGATE",
            "PREDICT",
            "RECOMMEND",
            "DECIDE",
            "EXPLAIN",
            "OPTIMIZE",
        }

        valid_business_areas = {
            "FINANCE",
            "SALES",
            "MARKETING",
            "CUSTOMER",
            "OPERATIONS",
            "PRODUCT",
            "HR",
            "PROCUREMENT",
            "STRATEGY",
            "RISK",
            "TECHNOLOGY",
            "COMPLIANCE",
            "MARKET",
            "GENERAL",
        }

        if question_type not in valid_question_types:
            question_type = "ANALYZE"

        if business_area not in valid_business_areas:
            business_area = "GENERAL"

        if not isinstance(
            specialist_agents,
            list
        ):
            specialist_agents = []

        validated_agents = []

        for agent_name in specialist_agents:

            agent_name = str(
                agent_name
            ).strip()

            if (
                agent_name in available_agents
                and agent_name not in validated_agents
            ):
                validated_agents.append(
                    agent_name
                )

        return {
            "question_type": question_type,
            "business_area": business_area,
            "specialist_agents": validated_agents,
            "reasoning": reasoning
        }

    # ============================================================
    # CRITIQUE VALIDATION
    # ============================================================

    def _validate_critique_result(
        self,
        result: dict
    ) -> dict:

        status = str(
            result.get(
                "status",
                "REVIEW"
            )
        ).upper()

        if status not in {
            "PASS",
            "REVIEW"
        }:
            status = "REVIEW"

        overall_assessment = str(
            result.get(
                "overall_assessment",
                ""
            )
        ).strip()

        conflicts = result.get(
            "conflicts",
            []
        )

        if not isinstance(
            conflicts,
            list
        ):
            conflicts = []

        validated_conflicts = []

        for conflict in conflicts:

            if not isinstance(
                conflict,
                dict
            ):
                continue

            conflict_type = str(
                conflict.get(
                    "type",
                    "TRUE_CONFLICT"
                )
            ).upper()

            if conflict_type not in {
                "TRUE_CONFLICT",
                "COMPLEMENTARY",
                "INSUFFICIENT_EVIDENCE"
            }:
                conflict_type = "TRUE_CONFLICT"

            agents = conflict.get(
                "agents",
                []
            )

            if not isinstance(
                agents,
                list
            ):
                agents = []

            validated_conflicts.append(
                {
                    "type": conflict_type,
                    "agents": [
                        str(agent)
                        for agent in agents
                    ],
                    "description": str(
                        conflict.get(
                            "description",
                            ""
                        )
                    ),
                    "material": bool(
                        conflict.get(
                            "material",
                            False
                        )
                    )
                }
            )

        complementary_findings = result.get(
            "complementary_findings",
            []
        )

        if not isinstance(
            complementary_findings,
            list
        ):
            complementary_findings = []

        validated_complementary = []

        for item in complementary_findings:

            if not isinstance(
                item,
                dict
            ):
                continue

            agents = item.get(
                "agents",
                []
            )

            if not isinstance(
                agents,
                list
            ):
                agents = []

            validated_complementary.append(
                {
                    "agents": [
                        str(agent)
                        for agent in agents
                    ],
                    "description": str(
                        item.get(
                            "description",
                            ""
                        )
                    )
                }
            )

        evidence_gaps = self._ensure_string_list(
            result.get(
                "evidence_gaps",
                []
            )
        )

        reasoning_issues = self._ensure_string_list(
            result.get(
                "reasoning_issues",
                []
            )
        )

        confidence = result.get(
            "confidence",
            0.0
        )

        try:
            confidence = float(
                confidence
            )
        except (
            TypeError,
            ValueError
        ):
            confidence = 0.0

        confidence = max(
            0.0,
            min(
                1.0,
                confidence
            )
        )

        # Force REVIEW when Gemini identifies a material
        # true conflict or reasoning/evidence issue.

        material_conflict = any(
            conflict["type"] == "TRUE_CONFLICT"
            and conflict["material"]
            for conflict in validated_conflicts
        )

        if (
            material_conflict
            or evidence_gaps
            or reasoning_issues
        ):
            status = "REVIEW"

        return {
            "status": status,
            "overall_assessment": overall_assessment,
            "conflicts": validated_conflicts,
            "complementary_findings": validated_complementary,
            "evidence_gaps": evidence_gaps,
            "reasoning_issues": reasoning_issues,
            "confidence": confidence
        }

    # ============================================================
    # SYNTHESIS VALIDATION
    # ============================================================

    def _validate_synthesis_result(
        self,
        result: dict
    ) -> dict:

        answer = str(
            result.get(
                "answer",
                ""
            )
        ).strip()

        recommendation_value = result.get(
            "recommendation"
        )

        if recommendation_value is None:

            recommendation = None

        else:

            recommendation = str(
                recommendation_value
            ).strip()

            if not recommendation:
                recommendation = None

        confidence = result.get(
            "confidence",
            0.0
        )

        try:
            confidence = float(
                confidence
            )
        except (
            TypeError,
            ValueError
        ):
            confidence = 0.0

        confidence = max(
            0.0,
            min(
                1.0,
                confidence
            )
        )

        key_factors = self._ensure_string_list(
            result.get(
                "key_factors",
                []
            )
        )

        risks = self._ensure_string_list(
            result.get(
                "risks",
                []
            )
        )

        assumptions = self._ensure_string_list(
            result.get(
                "assumptions",
                []
            )
        )

        agent_conflicts = self._ensure_string_list(
            result.get(
                "agent_conflicts",
                []
            )
        )

        evidence = result.get(
            "evidence",
            []
        )

        if not isinstance(
            evidence,
            list
        ):
            evidence = []

        validated_evidence = []

        for item in evidence:

            if not isinstance(
                item,
                dict
            ):
                continue

            validated_evidence.append(
                {
                    "source": str(
                        item.get(
                            "source",
                            ""
                        )
                    ),
                    "factor": str(
                        item.get(
                            "factor",
                            ""
                        )
                    ),
                    "value": item.get(
                        "value"
                    ),
                    "reason": str(
                        item.get(
                            "reason",
                            ""
                        )
                    )
                }
            )

        return {
            "answer": answer,
            "recommendation": recommendation,
            "confidence": confidence,
            "key_factors": key_factors,
            "risks": risks,
            "assumptions": assumptions,
            "evidence": validated_evidence,
            "agent_conflicts": agent_conflicts
        }

    # ============================================================
    # STRING LIST VALIDATION
    # ============================================================

    def _ensure_string_list(
        self,
        value
    ) -> list[str]:

        if not isinstance(
            value,
            list
        ):
            return []

        return [
            str(item)
            for item in value
            if item is not None
        ]

    # ============================================================
    # LEGACY CREDIT DECISION ANALYSIS
    # ============================================================

    def analyze_decision(
        self,
        customer_data: dict,
        agent_results: list
    ):

        prompt = f"""
You are an AI business decision analyst.

You are reviewing a business credit-limit decision.

CUSTOMER DATA:
{customer_data}

AGENT ASSESSMENTS:
{agent_results}

Analyze the decision and provide a concise business explanation.

Your response must contain:

1. Overall Assessment
2. Key Positive Factors
3. Key Risk Factors
4. Important Considerations
5. Explanation of the Decision

Rules:

- Use only the information supplied above.
- Do not invent financial information.
- Do not invent customer information.
- Do not change any numerical scores.
- Do not calculate new scores.
- Do not change the final decision.
- Clearly distinguish facts from interpretation.
- Keep the explanation professional and suitable for an audit record.
- Keep the response under 500 words.
"""

        try:

            interaction = self.client.interactions.create(
                model=self.model,
                input=prompt
            )

            return interaction.output_text

        except Exception as e:

            return (
                "AI analysis was unavailable for this decision. "
                "Deterministic agent results were successfully "
                "generated. "
                f"LLM error: {str(e)}"
            )