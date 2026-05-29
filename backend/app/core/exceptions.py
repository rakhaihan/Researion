import logging

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from jose import JWTError
from sqlalchemy.exc import SQLAlchemyError
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.config import get_settings

logger = logging.getLogger("researion.errors")


def _error_content(request: Request, detail: str, code: str) -> dict:
    settings = get_settings()
    payload: dict = {"detail": detail, "code": code}
    request_id = getattr(request.state, "request_id", None)
    if request_id:
        payload["request_id"] = request_id
    if settings.debug:
        payload["debug"] = True
    return payload


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        logger.warning("Validation error path=%s errors=%s", request.url.path, exc.errors())
        content = _error_content(request, "Validation failed", "validation_error")
        if get_settings().debug:
            content["errors"] = exc.errors()
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content=content,
        )

    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(
        request: Request, exc: StarletteHTTPException
    ) -> JSONResponse:
        detail = exc.detail if isinstance(exc.detail, str) else "Request failed"
        return JSONResponse(
            status_code=exc.status_code,
            content=_error_content(request, detail, "http_error"),
        )

    @app.exception_handler(JWTError)
    async def jwt_exception_handler(request: Request, exc: JWTError) -> JSONResponse:
        logger.warning("JWT error: %s", exc)
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content=_error_content(request, "Could not validate credentials", "auth_error"),
        )

    @app.exception_handler(SQLAlchemyError)
    async def database_exception_handler(
        request: Request, exc: SQLAlchemyError
    ) -> JSONResponse:
        logger.exception("Database error path=%s", request.url.path)
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content=_error_content(request, "Database unavailable", "database_error"),
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        logger.exception("Unhandled error path=%s", request.url.path)
        settings = get_settings()
        detail = str(exc) if settings.debug else "Internal server error"
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=_error_content(request, detail, "internal_error"),
        )
