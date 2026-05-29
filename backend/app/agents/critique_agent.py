import json
from typing import Any

from app.agents.base import BaseAgent
from app.utils.prompts import CRITIQUE_SYSTEM_PROMPT


class CritiqueAgent(BaseAgent):
    name = "critique_agent"

    async def run(self, analysis: dict[str, Any], topic: str, **kwargs: Any) -> dict[str, Any]:
        user_prompt = (
            f"Research topic: {topic}\n"
            f"Analysis to critique:\n{json.dumps(analysis, indent=2)}"
        )

        fallback = {
            "weaknesses": ["Analysis relies on secondary sources only."],
            "missing_perspectives": ["Regional or sector-specific viewpoints may be underrepresented."],
            "possible_bias": ["Confirmation bias toward mainstream narratives."],
            "confidence_level": "medium",
        }

        return await self.llm.generate_json(
            CRITIQUE_SYSTEM_PROMPT,
            user_prompt,
            fallback=fallback,
        )
