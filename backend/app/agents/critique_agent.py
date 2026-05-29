import json
from typing import Any

from app.agents.base import BaseAgent
from app.utils.citations import build_citation_catalog
from app.utils.prompts import CRITIQUE_SYSTEM_PROMPT


class CritiqueAgent(BaseAgent):
    name = "critique_agent"

    async def run(
        self,
        analysis: dict[str, Any],
        topic: str,
        sources: list[dict[str, Any]] | None = None,
        summaries: list[dict[str, Any]] | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        catalog = build_citation_catalog(sources or [])
        low_cred = [
            s.get("citation_key")
            for s in (sources or [])
            if float(s.get("credibility_score", 10)) < 5
        ]

        user_prompt = (
            f"Research topic: {topic}\n\n"
            f"Source catalog:\n{catalog}\n\n"
            f"Low credibility sources (score < 5): {low_cred}\n\n"
            f"Summaries:\n{json.dumps(summaries or [], indent=2)}\n\n"
            f"Analysis to critique:\n{json.dumps(analysis, indent=2)}\n\n"
            "Check for uncited claims, single-source reliance, outdated sources, and bias."
        )

        fallback = {
            "weaknesses": ["Analysis relies on secondary sources only."],
            "missing_perspectives": [
                "Regional or sector-specific viewpoints may be underrepresented."
            ],
            "possible_bias": ["Confirmation bias toward mainstream narratives."],
            "over_reliance_on_single_source": len(sources or []) < 3,
            "uncited_claims": [],
            "outdated_sources": [],
            "low_credibility_sources": low_cred,
            "missing_perspective_areas": ["Regulatory outlook"],
            "confidence_level": "medium",
        }

        return await self.llm.generate_json(
            CRITIQUE_SYSTEM_PROMPT,
            user_prompt,
            fallback=fallback,
        )
