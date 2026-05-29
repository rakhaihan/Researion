from typing import Any

from app.agents.base import BaseAgent
from app.schemas.agent_outputs import PlannerOutput, ResearchQuestionPlan
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
        fallback = PlannerOutput(
            questions=[
                ResearchQuestionPlan(
                    question=f"What is the current situation regarding {topic}?",
                    priority=1,
                    rationale="Establish baseline context.",
                ),
                ResearchQuestionPlan(
                    question=f"What are the key drivers affecting {topic}?",
                    priority=2,
                    rationale="Identify causal factors.",
                ),
                ResearchQuestionPlan(
                    question=f"What are the main risks related to {topic}?",
                    priority=3,
                    rationale="Surface downside scenarios.",
                ),
            ]
        )

        user_prompt = (
            f"Topic: {topic}\n"
            f"Research Type: {research_type}\n"
            f"Depth: {depth}\n"
            "Generate 5-7 focused research questions with rationale."
        )

        output, _warnings = await self.llm.generate_structured(
            PLANNER_SYSTEM_PROMPT,
            user_prompt,
            PlannerOutput,
            fallback,
        )
        return [q.model_dump() for q in output.questions]
