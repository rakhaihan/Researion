from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import health, jobs, reports, research
from app.core.config import get_settings
from app.core.logging import setup_logging
from app.core.redis import close_arq_pool, get_arq_pool
from app.db.database import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging()
    await init_db()
    await get_arq_pool()
    yield
    await close_arq_pool()


def create_app() -> FastAPI:
    settings = get_settings()

    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description="Multi-Agent Research Assistant API",
        lifespan=lifespan,
        docs_url="/docs",
        redoc_url="/redoc",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(health.router, prefix=settings.api_prefix)
    app.include_router(research.router, prefix=settings.api_prefix)
    app.include_router(reports.router, prefix=settings.api_prefix)
    app.include_router(jobs.router, prefix=settings.api_prefix)

    return app


app = create_app()
