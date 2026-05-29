from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.core.config import get_settings
from app.services.health_service import HealthService

router = APIRouter(tags=["health"])
health_service = HealthService()


@router.get("/health")
async def health_check() -> dict[str, str]:
    settings = get_settings()
    return {
        "status": "ok",
        "service": "researion-backend",
        "environment": settings.environment,
    }


@router.get("/health/live")
async def liveness_check() -> dict[str, str]:
    return {"status": "alive", "service": "researion-backend"}


@router.get("/health/ready")
async def readiness_check(db: AsyncSession = Depends(get_db)) -> JSONResponse:
    db_ok, db_error = await health_service.check_database(db)
    redis_ok, redis_error = await health_service.check_redis()
    queue_ok, queue_error = await health_service.check_worker_queue()

    checks = {
        "database": {"ok": db_ok, "error": db_error},
        "redis": {"ok": redis_ok, "error": redis_error},
        "worker_queue": {"ok": queue_ok, "error": queue_error},
    }
    ready = db_ok and redis_ok and queue_ok

    payload = {
        "status": "ready" if ready else "not_ready",
        "checks": checks,
    }
    return JSONResponse(
        status_code=status.HTTP_200_OK if ready else status.HTTP_503_SERVICE_UNAVAILABLE,
        content=payload,
    )
