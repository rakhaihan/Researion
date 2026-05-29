import json
import logging
import time
import uuid
from collections.abc import Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from app.core.config import get_settings

logger = logging.getLogger("researion.request")


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        settings = get_settings()
        request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
        request.state.request_id = request_id

        start = time.perf_counter()
        response: Response | None = None
        error_message: str | None = None

        try:
            response = await call_next(request)
            return response
        except Exception as exc:
            error_message = str(exc)
            raise
        finally:
            duration_ms = round((time.perf_counter() - start) * 1000, 2)
            status_code = response.status_code if response is not None else 500
            user_id = getattr(request.state, "user_id", None)
            job_id = getattr(request.state, "job_id", None)
            research_id = getattr(request.state, "research_id", None)

            payload = {
                "event": "http_request",
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "status_code": status_code,
                "duration_ms": duration_ms,
                "user_id": str(user_id) if user_id else None,
                "job_id": job_id,
                "research_id": str(research_id) if research_id else None,
                "error_message": error_message,
            }

            if settings.log_json:
                logger.info(json.dumps({k: v for k, v in payload.items() if v is not None}))
            else:
                logger.info(
                    "%s %s %s %.2fms request_id=%s user_id=%s",
                    request.method,
                    request.url.path,
                    status_code,
                    duration_ms,
                    request_id,
                    user_id or "-",
                )

            if response is not None:
                response.headers["X-Request-ID"] = request_id
