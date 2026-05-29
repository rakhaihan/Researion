from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings

try:
    import redis.asyncio as aioredis
except ImportError:  # pragma: no cover
    aioredis = None


class HealthService:
    async def check_database(self, db: AsyncSession) -> tuple[bool, str | None]:
        try:
            await db.execute(text("SELECT 1"))
            return True, None
        except Exception as exc:
            return False, str(exc)

    async def check_redis(self) -> tuple[bool, str | None]:
        if aioredis is None:
            return False, "redis client unavailable"
        settings = get_settings()
        client = aioredis.from_url(settings.redis_url, decode_responses=True)
        try:
            pong = await client.ping()
            if not pong:
                return False, "Redis ping failed"
            return True, None
        except Exception as exc:
            return False, str(exc)
        finally:
            await client.aclose()

    async def check_worker_queue(self) -> tuple[bool, str | None]:
        """Redis availability is required for the Arq worker queue."""
        return await self.check_redis()
