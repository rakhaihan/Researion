import json
from typing import Any

from app.agents.base import BaseAgent
from app.utils.prompts import ANALYST_SYSTEM_PROMPT


class AnalystAgent(BaseAgent):
    name = "analyst_agent"

    async def run(
        self,
        summaries: list[dict[str, Any]],
        topic: str,
        **kwargs: Any,
    ) -> dict[str, Any]:
        user_prompt = (
            f"Research topic: {topic}\n"
            f"Summaries:\n{json.dumps(summaries, indent=2)}"
        )

        fallback = {
            "analysis": f"Synthesis of available sources on {topic}.",
            "patterns": ["Multiple sources highlight similar trends."],
            "comparison": "Sources generally align on major themes with some divergence on timing.",
            "opportunities": ["Further primary research recommended."],
            "risks": ["Limited source diversity may affect conclusions."],
        }

        return await self.llm.generate_json(
            ANALYST_SYSTEM_PROMPT,
            user_prompt,
            fallback=fallback,
        )
