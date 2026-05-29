from collections.abc import Awaitable, Callable
from typing import Any, TypedDict

from langgraph.graph import END, StateGraph

from app.agents.analyst_agent import AnalystAgent
from app.agents.critique_agent import CritiqueAgent
from app.agents.planner_agent import PlannerAgent
from app.agents.report_writer_agent import ReportWriterAgent
from app.agents.search_agent import SearchAgent
from app.agents.source_evaluator_agent import SourceEvaluatorAgent
from app.agents.summarizer_agent import SummarizerAgent
from app.core.config import get_settings
from app.core.logging import get_logger
from app.db.models import ResearchStep, STEP_PROGRESS

logger = get_logger(__name__)

ProgressCallback = Callable[[str, int], Awaitable[None]]


class ResearchState(TypedDict, total=False):
    topic: str
    research_type: str
    depth: str
    status: str
    questions: list[dict[str, Any]]
    sources: list[dict[str, Any]]
    evaluated_sources: list[dict[str, Any]]
    summaries: list[dict[str, Any]]
    analysis: dict[str, Any]
    critique: dict[str, Any]
    report: dict[str, Any]
    error: str | None


class ResearchWorkflow:
    def __init__(self) -> None:
        self.settings = get_settings()
        self.planner = PlannerAgent()
        self.search_agent = SearchAgent()
        self.evaluator = SourceEvaluatorAgent()
        self.summarizer = SummarizerAgent()
        self.analyst = AnalystAgent()
        self.critique_agent = CritiqueAgent()
        self.report_writer = ReportWriterAgent()
        self._on_progress: ProgressCallback | None = None
        self.graph = self._build_graph()

    def _build_graph(self):
        workflow = StateGraph(ResearchState)

        workflow.add_node("plan", self._plan_node)
        workflow.add_node("search", self._search_node)
        workflow.add_node("evaluate", self._evaluate_node)
        workflow.add_node("summarize", self._summarize_node)
        workflow.add_node("analyze", self._analyze_node)
        workflow.add_node("run_critique", self._critique_node)
        workflow.add_node("write_report", self._write_report_node)

        workflow.set_entry_point("plan")
        workflow.add_edge("plan", "search")
        workflow.add_edge("search", "evaluate")
        workflow.add_edge("evaluate", "summarize")
        workflow.add_edge("summarize", "analyze")
        workflow.add_edge("analyze", "run_critique")
        workflow.add_edge("run_critique", "write_report")
        workflow.add_edge("write_report", END)

        return workflow.compile()

    async def run(
        self,
        topic: str,
        research_type: str,
        depth: str,
        on_progress: ProgressCallback | None = None,
    ) -> ResearchState:
        self._on_progress = on_progress
        initial_state: ResearchState = {
            "topic": topic,
            "research_type": research_type,
            "depth": depth,
            "status": "planning",
        }
        result = await self.graph.ainvoke(initial_state)
        if on_progress:
            await on_progress(
                ResearchStep.COMPLETED.value,
                STEP_PROGRESS[ResearchStep.COMPLETED.value],
            )
        return result

    async def _emit_progress(self, step: str) -> None:
        if self._on_progress:
            await self._on_progress(step, STEP_PROGRESS[step])

    async def _plan_node(self, state: ResearchState) -> dict[str, Any]:
        await self._emit_progress(ResearchStep.PLANNING.value)
        logger.info("Running planner agent for topic: %s", state["topic"])
        questions = await self.planner.run(
            topic=state["topic"],
            research_type=state["research_type"],
            depth=state["depth"],
        )
        return {"questions": questions, "status": "searching"}

    async def _search_node(self, state: ResearchState) -> dict[str, Any]:
        await self._emit_progress(ResearchStep.SEARCHING.value)
        logger.info("Running search agent")
        sources = await self.search_agent.run(
            questions=state["questions"],
            topic=state["topic"],
        )
        return {"sources": sources, "status": "evaluating"}

    async def _evaluate_node(self, state: ResearchState) -> dict[str, Any]:
        await self._emit_progress(ResearchStep.EVALUATING_SOURCES.value)
        logger.info("Running source evaluator agent")
        evaluated = await self.evaluator.run(sources=state["sources"])
        return {"evaluated_sources": evaluated, "status": "summarizing"}

    async def _summarize_node(self, state: ResearchState) -> dict[str, Any]:
        await self._emit_progress(ResearchStep.SUMMARIZING.value)
        logger.info("Running summarizer agent")
        summaries = await self.summarizer.run(
            sources=state["evaluated_sources"],
            min_credibility=self.settings.min_credibility_score,
        )
        return {"summaries": summaries, "status": "analyzing"}

    async def _analyze_node(self, state: ResearchState) -> dict[str, Any]:
        await self._emit_progress(ResearchStep.ANALYZING.value)
        logger.info("Running analyst agent")
        analysis = await self.analyst.run(
            summaries=state["summaries"],
            topic=state["topic"],
            sources=state["evaluated_sources"],
        )
        return {"analysis": analysis, "status": "critiquing"}

    async def _critique_node(self, state: ResearchState) -> dict[str, Any]:
        await self._emit_progress(ResearchStep.CRITIQUING.value)
        logger.info("Running critique agent")
        critique = await self.critique_agent.run(
            analysis=state["analysis"],
            topic=state["topic"],
            sources=state["evaluated_sources"],
            summaries=state["summaries"],
        )
        return {"critique": critique, "status": "writing"}

    async def _write_report_node(self, state: ResearchState) -> dict[str, Any]:
        await self._emit_progress(ResearchStep.WRITING_REPORT.value)
        logger.info("Running report writer agent")
        report = await self.report_writer.run(
            topic=state["topic"],
            research_type=state["research_type"],
            questions=state["questions"],
            summaries=state["summaries"],
            analysis=state["analysis"],
            critique=state["critique"],
            sources=state["evaluated_sources"],
        )
        return {"report": report, "status": "completed"}
