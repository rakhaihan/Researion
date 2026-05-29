import json
from typing import Any

from app.agents.base import BaseAgent
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
        user_prompt = (
            f"Topic: {topic}\n"
            f"Research Type: {research_type}\n"
            f"Questions: {json.dumps(questions, indent=2)}\n"
            f"Summaries: {json.dumps(summaries, indent=2)}\n"
            f"Analysis: {json.dumps(analysis, indent=2)}\n"
            f"Critique: {json.dumps(critique, indent=2)}\n"
            f"Sources: {json.dumps(sources, indent=2)}\n"
        )

        fallback = self._build_fallback_report(
            topic, research_type, questions, analysis, critique, sources
        )

        report = await self.llm.generate_json(
            REPORT_WRITER_SYSTEM_PROMPT,
            user_prompt,
            fallback=fallback,
        )

        report["markdown_content"] = self._to_markdown(report, topic, research_type)
        return report

    def _build_fallback_report(
        self,
        topic: str,
        research_type: str,
        questions: list[dict[str, Any]],
        analysis: dict[str, Any],
        critique: dict[str, Any],
        sources: list[dict[str, Any]],
    ) -> dict[str, Any]:
        return {
            "title": f"Research Report: {topic}",
            "executive_summary": analysis.get("analysis", f"Research on {topic}."),
            "research_questions": [q["question"] for q in questions],
            "methodology": f"Multi-agent workflow with {research_type} focus.",
            "key_findings": analysis.get("patterns", []),
            "detailed_analysis": analysis.get("analysis", ""),
            "risks_and_limitations": critique.get("weaknesses", []),
            "opposing_views": critique.get("missing_perspectives", []),
            "conclusion": f"Further monitoring of {topic} is recommended.",
            "sources": [
                {"title": s.get("title", "Source"), "url": s.get("url", "")}
                for s in sources
            ],
        }

    def _to_markdown(self, report: dict[str, Any], topic: str, research_type: str) -> str:
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
                "## Sources",
            ]
        )
        for source in report.get("sources", []):
            if isinstance(source, dict):
                lines.append(f"- [{source.get('title', 'Source')}]({source.get('url', '')})")
            else:
                lines.append(f"- {source}")

        return "\n".join(lines)
