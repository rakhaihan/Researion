from typing import Any

from app.agents.base import BaseAgent
from app.utils.prompts import SEARCH_EVALUATOR_SYSTEM_PROMPT
from app.utils.url_utils import extract_domain


class SourceEvaluatorAgent(BaseAgent):
    name = "source_evaluator_agent"

    async def run(self, sources: list[dict[str, Any]], **kwargs: Any) -> list[dict[str, Any]]:
        evaluated: list[dict[str, Any]] = []

        for source in sources:
            domain = extract_domain(source.get("url", ""))
            user_prompt = (
                f"Citation key: {source.get('citation_key', 'N/A')}\n"
                f"Research question: {source.get('question', 'N/A')}\n"
                f"Title: {source.get('title')}\n"
                f"URL: {source.get('url')}\n"
                f"Domain: {domain}\n"
                f"Snippet: {source.get('snippet')}\n"
                f"Published date: {source.get('published_date', 'unknown')}\n"
                f"Source type hint: {source.get('source_type', 'web')}\n"
            )

            fallback = {
                "credibility_score": 6.5,
                "source_type": source.get("source_type", "web"),
                "credibility_reason": (
                    f"Moderate credibility for {domain or 'unknown domain'} based on snippet-only review."
                ),
                "is_primary_source": False,
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
                    "credibility_reason": result.get(
                        "credibility_reason",
                        result.get("evaluation_notes", ""),
                    ),
                    "source_type": result.get("source_type", source.get("source_type", "web")),
                    "is_primary_source": result.get("is_primary_source", False),
                    "evaluation_notes": result.get("evaluation_notes", ""),
                }
            )

        return evaluated
