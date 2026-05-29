from typing import Any

from app.agents.base import BaseAgent
from app.utils.prompts import SEARCH_EVALUATOR_SYSTEM_PROMPT


class SourceEvaluatorAgent(BaseAgent):
    name = "source_evaluator_agent"

    async def run(self, sources: list[dict[str, Any]], **kwargs: Any) -> list[dict[str, Any]]:
        evaluated: list[dict[str, Any]] = []

        for source in sources:
            user_prompt = (
                f"Research question: {source.get('question', 'N/A')}\n"
                f"Title: {source.get('title')}\n"
                f"URL: {source.get('url')}\n"
                f"Snippet: {source.get('snippet')}\n"
                f"Published date: {source.get('published_date', 'unknown')}\n"
            )

            fallback = {
                "credibility_score": 6.5,
                "source_type": source.get("source_type", "web"),
                "evaluation_notes": "Fallback evaluation due to missing LLM response.",
            }

            result = await self.llm.generate_json(
                SEARCH_EVALUATOR_SYSTEM_PROMPT,
                user_prompt,
                fallback=fallback,
            )

            evaluated.append(
                {
                    **source,
                    "credibility_score": float(result.get("credibility_score", 6.5)),
                    "source_type": result.get("source_type", source.get("source_type", "web")),
                    "evaluation_notes": result.get("evaluation_notes", ""),
                }
            )

        return evaluated
