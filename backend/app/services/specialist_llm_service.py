from typing import Any

from google import genai

from ..config import settings


class SpecialistLLMService:
    """
    Gemini service used by domain specialist agents.

    The specialist is given:
    - business question
    - specialist domain
    - business context
    - objectives
    - constraints

    It analyzes only the supplied information and does not
    invent missing business facts.
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

    def analyze(
        self,
        question: str,
        domain: str,
        context: dict[str, Any],
        objectives: list[str],
        constraints: list[str]
    ) -> dict[str, Any]:

        prompt = f"""
You are the {domain} Specialist Agent in a
multi-agent business decision engine.

Your task is to analyze the business question specifically
from the perspective of the {domain} domain.

BUSINESS QUESTION:
{question}

DOMAIN:
{domain}

BUSINESS CONTEXT:
{context}

OBJECTIVES:
{objectives}

CONSTRAINTS:
{constraints}

IMPORTANT RULES:

- Use only the information supplied above.
- Do not invent business facts.
- Do not invent metrics.
- Do not invent causes that are not supported by the data.
- Clearly distinguish observed facts from interpretation.
- Identify missing information when it prevents a reliable conclusion.
- Focus only on your domain.
- Provide useful analytical findings for a later Synthesis Agent.
- Do not make the final overall business decision.
- Do not pretend certainty when evidence is incomplete.

Return ONLY valid JSON.

Required structure:

{{
    "assessment": "Concise domain-specific assessment.",
    "recommendation": "Domain-specific recommendation or null.",
    "confidence": 0.0,
    "findings": [
        {{
            "factor": "factor name",
            "value": "observed value",
            "impact": "positive",
            "reason": "Why this matters."
        }}
    ],
    "missing_information": [
        "Information required for stronger analysis."
    ]
}}

CONFIDENCE:

Use a value from 0 to 1.

Confidence represents how strongly the supplied evidence
supports this domain assessment. It is not a statistical
probability.
"""

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
                "Gemini returned an empty specialist analysis."
            )

        return self._parse_json(
            output_text
        )

    def _parse_json(
        self,
        output_text: str
    ) -> dict[str, Any]:

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

        import json

        result = json.loads(
            cleaned
        )

        if not isinstance(
            result,
            dict
        ):
            raise ValueError(
                "Specialist response must be a JSON object."
            )

        return result