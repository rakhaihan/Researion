from urllib.parse import parse_qsl, urlparse, urlunparse

TRACKING_PARAMS = frozenset(
    {
        "utm_source",
        "utm_medium",
        "utm_campaign",
        "utm_term",
        "utm_content",
        "fbclid",
        "gclid",
        "mc_cid",
        "mc_eid",
        "ref",
        "source",
    }
)


def normalize_url(url: str) -> str:
    """Normalize URL for deduplication: strip tracking params, trailing slash, lowercase host."""
    if not url:
        return ""

    parsed = urlparse(url.strip())
    if not parsed.scheme or not parsed.netloc:
        return url.strip().lower()

    netloc = parsed.netloc.lower()
    if netloc.startswith("www."):
        netloc = netloc[4:]

    filtered_query = [
        (key, value)
        for key, value in parse_qsl(parsed.query, keep_blank_values=True)
        if key.lower() not in TRACKING_PARAMS
    ]
    query = "&".join(f"{key}={value}" for key, value in sorted(filtered_query))

    path = parsed.path.rstrip("/") or ""

    normalized = urlunparse(
        (
            parsed.scheme.lower(),
            netloc,
            path,
            "",
            query,
            "",
        )
    )
    return normalized


def extract_domain(url: str) -> str:
    if not url:
        return ""
    parsed = urlparse(url)
    netloc = parsed.netloc.lower()
    if netloc.startswith("www."):
        netloc = netloc[4:]
    return netloc
