import json
import logging
import sys
from datetime import UTC, datetime
from typing import Any

from app.core.config import get_settings


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "timestamp": datetime.now(UTC).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)
        for key in ("request_id", "user_id", "job_id", "research_id"):
            if hasattr(record, key):
                payload[key] = getattr(record, key)
        return json.dumps(payload)


def setup_logging() -> None:
    settings = get_settings()
    level = logging.DEBUG if settings.debug else logging.INFO

    handler = logging.StreamHandler(sys.stdout)
    if settings.log_json:
        handler.setFormatter(JsonFormatter())
    else:
        handler.setFormatter(
            logging.Formatter("%(asctime)s | %(levelname)s | %(name)s | %(message)s")
        )

    root = logging.getLogger()
    root.handlers.clear()
    root.addHandler(handler)
    root.setLevel(level)

    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)


def log_extra(logger: logging.Logger, message: str, **kwargs: Any) -> None:
    settings = get_settings()
    if settings.log_json:
        logger.info(message, extra=kwargs)
    else:
        extra = " ".join(f"{key}={value}" for key, value in kwargs.items())
        logger.info("%s | %s", message, extra)
