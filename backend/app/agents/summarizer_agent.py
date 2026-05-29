from typing import Any

from app.agents.base import BaseAgent
from app.schemas.agent_outputs import SourceSummaryItem
from app.utils.prompts import SUMMARIZER_SYSTEM_PROMPT


class SummarizerAgent(BaseAgent):
    name = "summarizer_agent"

    async def run(
        self,
        sources: list[dict[str, Any]],
        min_credibility: float = 5.0,
        **kwargs: Any,
    ) -> list[dict[str, Any]]:
        summaries: list[dict[str, Any]] = []

        credible_sources = [
            source
            for source in sources
            if float(source.get("credibility_score", 0)) >= min_credibility
        ]

        for source in credible_sources:
            citation_key = source.get("citation_key", "S1")
            user_prompt = (
                f"Citation key: {citation_key}\n"
                f"Title: {source.get('title')}\n"
                f"URL: {source.get('url')}\n"
                f"Snippet: {source.get('snippet')}\n"
                f"Question context: {source.get('question', 'N/A')}\n"
                f"Credibility: {source.get('credibility_score')}/10 — "
                f"{source.get('credibility_reason', '')}\n"
            )

            fallback = SourceSummaryItem(
                citation_key=citation_key,
                summary=source.get("snippet", "No summary available.") or "Insufficient evidence.",
                key_points=[f"[{citation_key}] {str(source.get('snippet', ''))[:200]}"],
                useful_quotes=[],
                limitations="Based on snippet only; full content not retrieved.",
                source_url=source.get("url"),
            )

            result, _ = await self.llm.generate_structured(
                SUMMARIZER_SYSTEM_PROMPT,
                user_prompt,
                SourceSummaryItem,
                fallback,
            )

            summaries.append(
                {
                    "citation_key": result.citation_key,
                    "source_url": source.get("url"),
                    "source_title": source.get("title"),
                    "summary": result.summary,
                    "key_points": result.key_points,
                    "useful_quotes": result.useful_quotes,
                    "limitations": result.limitations,
                }
            )

        return summaries
