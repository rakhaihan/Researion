import re
from urllib.parse import urlparse


def validate_topic(topic: str) -> str:
    cleaned = topic.strip()
    if len(cleaned) < 3:
        raise ValueError("Topic must be at least 3 characters long")
    if len(cleaned) > 500:
        raise ValueError("Topic must not exceed 500 characters")
    return cleaned


def is_valid_url(url: str) -> bool:
    try:
        result = urlparse(url)
        return all([result.scheme in {"http", "https"}, result.netloc])
    except Exception:
        return False


def sanitize_filename(name: str) -> str:
    cleaned = re.sub(r"[^\w\s-]", "", name).strip().lower()
    cleaned = re.sub(r"[-\s]+", "-", cleaned)
    return cleaned[:80] or "research-report"
