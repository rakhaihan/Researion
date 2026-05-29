from typing import Any

from app.agents.base import BaseAgent
from app.schemas.agent_outputs import SourceEvaluationItem
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

            fallback = SourceEvaluationItem(
                citation_key=source.get("citation_key"),
                url=source.get("url", ""),
                credibility_score=6.5,
                source_type=source.get("source_type", "web"),
                credibility_reason=(
                    f"Moderate credibility for {domain or 'unknown domain'} (fallback evaluation)."
                ),
                is_primary_source=False,
                evaluation_notes="Fallback evaluation due to missing LLM response.",
            )

            result, _ = await self.llm.generate_structured(
                SEARCH_EVALUATOR_SYSTEM_PROMPT,
                user_prompt,
                SourceEvaluationItem,
                fallback,
            )

            evaluated.append(
                {
                    **source,
                    "credibility_score": float(result.credibility_score),
                    "credibility_reason": result.credibility_reason,
                    "source_type": result.source_type,
                    "is_primary_source": result.is_primary_source,
                    "evaluation_notes": result.evaluation_notes or "",
                }
            )

        return evaluated
