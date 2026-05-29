import json
from typing import Any

from app.agents.base import BaseAgent
from app.utils.citations import build_citation_catalog
from app.utils.prompts import ANALYST_SYSTEM_PROMPT


class AnalystAgent(BaseAgent):
    name = "analyst_agent"

    async def run(
        self,
        summaries: list[dict[str, Any]],
        topic: str,
        sources: list[dict[str, Any]] | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        catalog = build_citation_catalog(sources or [])
        user_prompt = (
            f"Research topic: {topic}\n\n"
            f"Source catalog:\n{catalog}\n\n"
            f"Summaries:\n{json.dumps(summaries, indent=2)}\n\n"
            "Produce analysis with inline [Sx] citations for all important claims."
        )

        fallback = {
            "analysis": (
                f"Synthesis of available sources on {topic}. "
                "Multiple themes align across cited summaries [S1][S2]."
            ),
            "patterns": ["[S1] Multiple sources highlight similar trends."],
            "supporting_evidence": [
                {"claim": "Sources align on major themes", "citations": ["S1", "S2"]}
            ],
            "opportunities": ["[S1] Further primary research recommended."],
            "risks": ["[S2] Limited source diversity may affect conclusions."],
            "conflicting_signals": [],
            "confidence_level": "medium",
        }

        return await self.llm.generate_json(
            ANALYST_SYSTEM_PROMPT,
            user_prompt,
            fallback=fallback,
        )
