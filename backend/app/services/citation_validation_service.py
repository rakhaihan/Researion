import re
from collections import Counter

from app.schemas.quality import CitationValidationResult

CITATION_PATTERN = re.compile(r"\[S(\d+)\]")


class CitationValidationService:
    def validate(
        self,
        markdown_content: str,
        key_findings: list[str] | None,
        conclusion: str | None,
        valid_citation_keys: set[str],
        report_sources: list[dict] | None = None,
    ) -> CitationValidationResult:
        text_blocks = [markdown_content or ""]
        if key_findings:
            text_blocks.extend(key_findings)
        if conclusion:
            text_blocks.append(conclusion)
        full_text = "\n".join(text_blocks)

        cited_keys = {f"S{m}" for m in CITATION_PATTERN.findall(full_text)}
        invalid = sorted(cited_keys - valid_citation_keys)

        report_source_keys = set()
        if report_sources:
            for item in report_sources:
                key = item.get("citation_key") if isinstance(item, dict) else None
                if key:
                    report_source_keys.add(key)

        if report_source_keys:
            missing_in_report = valid_citation_keys - report_source_keys
        else:
            missing_in_report = set()
        warnings: list[str] = []
        recommendations: list[str] = []

        if invalid:
            warnings.append(f"Fictitious or unknown citations detected: {', '.join(invalid)}")
            recommendations.append(
                "Remove or replace invalid citation keys with catalog sources only."
            )

        findings = key_findings or []
        cited_findings = sum(1 for f in findings if CITATION_PATTERN.search(str(f)))
        coverage = (cited_findings / len(findings) * 100) if findings else 100.0
        if findings and coverage < 70:
            warnings.append(
                f"Only {coverage:.0f}% of key findings include citations (minimum 70% recommended)."
            )
            recommendations.append("Add [Sx] citations to key findings lacking source support.")

        single_source_warning = False
        if cited_keys:
            citation_usage = Counter(CITATION_PATTERN.findall(full_text))
            total_usage = sum(citation_usage.values())
            dominant_share = max(citation_usage.values()) / max(total_usage, 1)
            if citation_usage and dominant_share > 0.7:
                single_source_warning = True
                warnings.append("Report relies heavily on a single citation source.")
                recommendations.append(
                    "Incorporate additional sources to reduce single-source dependency."
                )

        conclusion_citations = set(CITATION_PATTERN.findall(conclusion or ""))
        if conclusion and conclusion.strip() and not conclusion_citations:
            warnings.append("Conclusion contains no inline citations.")
            recommendations.append("Support conclusion statements with [Sx] citations.")

        if missing_in_report:
            warnings.append(
                "Sources section missing entries for: "
                + ", ".join(sorted(missing_in_report)[:5])
            )

        is_valid = not invalid and coverage >= 50

        return CitationValidationResult(
            is_valid=is_valid,
            invalid_citations=invalid,
            missing_citation_warnings=warnings,
            source_coverage_score=round(coverage, 1),
            single_source_dependency_warning=single_source_warning,
            recommendations=recommendations,
        )
