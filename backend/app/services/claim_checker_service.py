import re

from app.schemas.quality import ClaimCheckResult

CITATION_PATTERN = re.compile(r"\[S\d+\]")

HIGH_RISK_PATTERNS = [
    r"\d+%",
    r"\d+\s*percent",
    r"meningkat",
    r"menurun",
    r"increase[ds]?",
    r"decrease[ds]?",
    r"terbesar",
    r"terbaik",
    r"largest",
    r"best",
    r"dominan",
    r"dominant",
    r"risiko utama",
    r"main risk",
    r"market leader",
    r"outperform",
    r"undervalued",
    r"overvalued",
]


class ClaimCheckerService:
    def __init__(self) -> None:
        self._risk_re = re.compile("|".join(HIGH_RISK_PATTERNS), re.IGNORECASE)

    def check(self, key_findings: list[str] | None, markdown_content: str | None = None) -> ClaimCheckResult:
        warnings: list[str] = []
        uncited: list[str] = []

        claims = list(key_findings or [])
        if markdown_content:
            for line in markdown_content.splitlines():
                line = line.strip()
                if line.startswith("- ") and len(line) > 20:
                    claims.append(line[2:])

        for claim in claims:
            claim_text = str(claim).strip()
            if len(claim_text) < 12:
                continue
            has_citation = bool(CITATION_PATTERN.search(claim_text))
            is_high_risk = bool(self._risk_re.search(claim_text))

            if not has_citation:
                if is_high_risk:
                    uncited.append(claim_text[:200])
                    warnings.append(
                        f"High-risk claim without citation: {claim_text[:120]}..."
                    )
                else:
                    warnings.append(
                        f"Key claim without citation: {claim_text[:120]}..."
                    )

        return ClaimCheckResult(warnings=warnings, uncited_high_risk_claims=uncited)
