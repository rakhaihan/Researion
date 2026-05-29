from typing import Any


def assign_citation_keys(sources: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Assign stable citation keys S1, S2, ... for a research project."""
    for index, source in enumerate(sources, start=1):
        source["citation_key"] = f"S{index}"
    return sources


def build_sources_markdown_section(sources: list[dict[str, Any]]) -> list[str]:
    """Build markdown Sources section with [Sx] Title — URL format."""
    lines = ["## Sources", ""]
    sorted_sources = sorted(
        sources,
        key=lambda item: int(item.get("citation_key", "S0")[1:] or 0)
        if item.get("citation_key", "").startswith("S")
        else 0,
    )
    for source in sorted_sources:
        key = source.get("citation_key", "")
        title = source.get("title", "Untitled")
        url = source.get("url", "")
        if source.get("source_type") == "document" or str(url).startswith("document://"):
            page = source.get("page_number")
            page_suffix = f", page {page}" if page else ""
            filename = source.get("original_filename") or title
            lines.append(f"[{key}] {filename}{page_suffix} — internal document")
        else:
            lines.append(f"[{key}] {title} — {url}")
    return lines


def build_citation_catalog(sources: list[dict[str, Any]]) -> str:
    """Human-readable catalog for LLM prompts."""
    lines: list[str] = []
    for source in sources:
        key = source.get("citation_key", "?")
        title = source.get("title", "Untitled")
        url = source.get("url", "")
        score = source.get("credibility_score", "N/A")
        lines.append(f"{key}: {title} ({url}) [credibility: {score}/10]")
    return "\n".join(lines)
