import logging
import sys
from typing import Any

from app.core.config import get_settings


def setup_logging() -> None:
    settings = get_settings()
    level = logging.DEBUG if settings.debug else logging.INFO

    logging.basicConfig(
        level=level,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)],
    )

    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)


def log_extra(logger: logging.Logger, message: str, **kwargs: Any) -> None:
    extra = " ".join(f"{key}={value}" for key, value in kwargs.items())
    logger.info("%s | %s", message, extra)
