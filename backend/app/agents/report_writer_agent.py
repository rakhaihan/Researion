import json
from typing import Any

from app.agents.base import BaseAgent
from app.schemas.agent_outputs import ReportSourceItem, ReportWriterOutput
from app.utils.citations import build_citation_catalog, build_sources_markdown_section
from app.utils.prompts import REPORT_WRITER_SYSTEM_PROMPT


class ReportWriterAgent(BaseAgent):
    name = "report_writer_agent"

    async def run(
        self,
        topic: str,
        research_type: str,
        questions: list[dict[str, Any]],
        summaries: list[dict[str, Any]],
        analysis: dict[str, Any],
        critique: dict[str, Any],
        sources: list[dict[str, Any]],
        **kwargs: Any,
    ) -> dict[str, Any]:
        catalog = build_citation_catalog(sources)
        user_prompt = (
            f"Topic: {topic}\n"
            f"Research Type: {research_type}\n\n"
            f"SOURCE CATALOG (use ONLY these citation keys):\n{catalog}\n\n"
            f"Questions: {json.dumps(questions, indent=2)}\n"
            f"Summaries: {json.dumps(summaries, indent=2)}\n"
            f"Analysis: {json.dumps(analysis, indent=2)}\n"
            f"Critique: {json.dumps(critique, indent=2)}\n\n"
            "Write the report with inline [Sx] citations. "
            "If evidence is insufficient, write 'insufficient evidence' — do not invent facts."
        )

        fallback = self._build_fallback_report(
            topic, research_type, questions, analysis, critique, sources
        )

        output, warnings = await self.llm.generate_structured(
            REPORT_WRITER_SYSTEM_PROMPT,
            user_prompt,
            ReportWriterOutput,
            fallback,
        )

        report = output.model_dump()
        if warnings:
            report.setdefault("risks_and_limitations", []).extend(warnings[:3])

        allowed_keys = {s.get("citation_key") for s in sources if s.get("citation_key")}
        report["sources"] = self._filter_sources(report.get("sources", []), sources, allowed_keys)
        report["markdown_content"] = self._to_markdown(report, topic, research_type, sources)

        if not report.get("markdown_content", "").strip():
            raise ValueError("Report writer produced empty markdown content")

        return report

    def _filter_sources(
        self,
        report_sources: list,
        db_sources: list[dict[str, Any]],
        allowed_keys: set[str],
    ) -> list[dict[str, Any]]:
        filtered: list[dict[str, Any]] = []
        for item in report_sources:
            if isinstance(item, dict):
                key = item.get("citation_key")
                if key in allowed_keys:
                    filtered.append(item)
            elif hasattr(item, "citation_key") and item.citation_key in allowed_keys:
                filtered.append(item.model_dump())
        if filtered:
            return filtered
        return [
            {
                "citation_key": s.get("citation_key", f"S{i + 1}"),
                "title": s.get("title", "Source"),
                "url": s.get("url", ""),
            }
            for i, s in enumerate(db_sources)
        ]

    def _build_fallback_report(
        self,
        topic: str,
        research_type: str,
        questions: list[dict[str, Any]],
        analysis: dict[str, Any],
        critique: dict[str, Any],
        sources: list[dict[str, Any]],
    ) -> ReportWriterOutput:
        citations = "".join(
            f"[{s.get('citation_key', '')}]" for s in sources[:2] if s.get("citation_key")
        )
        return ReportWriterOutput(
            title=f"Research Report: {topic}",
            executive_summary=(
                f"Research on {topic} synthesizes available evidence {citations or '[S1]'}. "
                f"{analysis.get('analysis', '')}"
            ),
            research_questions=[q["question"] for q in questions],
            methodology=(
                f"Multi-agent workflow with {research_type} focus, "
                "live search with citation tracking."
            ),
            key_findings=analysis.get("patterns", []) or ["[S1] Insufficient evidence for detailed findings."],
            detailed_analysis=analysis.get("analysis", "Insufficient evidence."),
            risks_and_limitations=critique.get("weaknesses", []),
            opposing_views=critique.get("missing_perspectives", []),
            conclusion=f"Further monitoring of {topic} is recommended {citations or '[S1]'}.",
            sources=[
                ReportSourceItem(
                    citation_key=s.get("citation_key", f"S{i + 1}"),
                    title=s.get("title", "Source"),
                    url=s.get("url", "https://example.com"),
                )
                for i, s in enumerate(sources)
            ],
        )

    def _to_markdown(
        self,
        report: dict[str, Any],
        topic: str,
        research_type: str,
        sources: list[dict[str, Any]],
    ) -> str:
        title = report.get("title", f"Research Report: {topic}")
        lines = [
            f"# {title}",
            "",
            f"**Research Type:** {research_type}",
            "",
            "## Executive Summary",
            report.get("executive_summary", ""),
            "",
            "## Research Questions",
        ]

        for question in report.get("research_questions", []):
            lines.append(f"- {question}")

        lines.extend(
            [
                "",
                "## Methodology",
                report.get("methodology", ""),
                "",
                "## Key Findings",
            ]
        )
        for finding in report.get("key_findings", []):
            lines.append(f"- {finding}")

        lines.extend(
            [
                "",
                "## Detailed Analysis",
                report.get("detailed_analysis", ""),
                "",
                "## Risks and Limitations",
            ]
        )
        for risk in report.get("risks_and_limitations", []):
            lines.append(f"- {risk}")

        lines.extend(["", "## Opposing Views"])
        for view in report.get("opposing_views", []):
            lines.append(f"- {view}")

        lines.extend(
            [
                "",
                "## Conclusion",
                report.get("conclusion", ""),
                "",
            ]
        )

        report_sources = report.get("sources", [])
        if report_sources and isinstance(report_sources[0], dict):
            catalog_sources = [
                {
                    "citation_key": item.get("citation_key", ""),
                    "title": item.get("title", "Source"),
                    "url": item.get("url", ""),
                }
                for item in report_sources
            ]
            lines.extend(build_sources_markdown_section(catalog_sources))
        else:
            lines.extend(build_sources_markdown_section(sources))

        return "\n".join(lines)
