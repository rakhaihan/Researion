from typing import Any

from app.agents.base import BaseAgent
from app.utils.prompts import PLANNER_SYSTEM_PROMPT


class PlannerAgent(BaseAgent):
    name = "planner_agent"

    async def run(
        self,
        topic: str,
        research_type: str,
        depth: str,
        **kwargs: Any,
    ) -> list[dict[str, Any]]:
        fallback = {
            "questions": [
                {"question": f"What is the current situation regarding {topic}?", "priority": 1},
                {"question": f"What are the key drivers affecting {topic}?", "priority": 2},
                {"question": f"What are the main risks related to {topic}?", "priority": 3},
                {"question": f"What are opposing views on {topic}?", "priority": 4},
                {"question": f"What conclusion can be drawn about {topic}?", "priority": 5},
            ]
        }

        user_prompt = (
            f"Topic: {topic}\n"
            f"Research Type: {research_type}\n"
            f"Depth: {depth}\n"
            "Generate 5-7 focused research questions."
        )

        result = await self.llm.generate_json(
            PLANNER_SYSTEM_PROMPT,
            user_prompt,
            fallback=fallback,
        )

        questions = result.get("questions", fallback["questions"])
        normalized: list[dict[str, Any]] = []
        for index, item in enumerate(questions, start=1):
            if isinstance(item, str):
                normalized.append({"question": item, "priority": index})
            elif isinstance(item, dict):
                normalized.append(
                    {
                        "question": item.get("question", f"Question {index}"),
                        "priority": item.get("priority", index),
                    }
                )
        return normalized
