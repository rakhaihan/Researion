from typing import Any

from app.agents.base import BaseAgent
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
            citation_key = source.get("citation_key", "")
            user_prompt = (
                f"Citation key: {citation_key}\n"
                f"Title: {source.get('title')}\n"
                f"URL: {source.get('url')}\n"
                f"Snippet: {source.get('snippet')}\n"
                f"Question context: {source.get('question', 'N/A')}\n"
                f"Credibility: {source.get('credibility_score')}/10 — "
                f"{source.get('credibility_reason', '')}\n"
            )

            fallback = {
                "summary": source.get("snippet", "No summary available."),
                "key_points": [
                    f"[{citation_key}] {source.get('snippet', '')[:200]}"
                ],
                "useful_quotes": [],
                "limitations": "Based on snippet only; full content not retrieved.",
                "citation_key": citation_key,
            }

            result = await self.llm.generate_json(
                SUMMARIZER_SYSTEM_PROMPT,
                user_prompt,
                fallback=fallback,
            )

            summaries.append(
                {
                    "citation_key": result.get("citation_key", citation_key),
                    "source_url": source.get("url"),
                    "source_title": source.get("title"),
                    "summary": result.get("summary", ""),
                    "key_points": result.get("key_points", []),
                    "useful_quotes": result.get("useful_quotes", []),
                    "limitations": result.get("limitations", ""),
                }
            )

        return summaries
