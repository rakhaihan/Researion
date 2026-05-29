"""Docker HEALTHCHECK helper: exit 0 when dependency is reachable."""
import asyncio
import sys

from sqlalchemy import text

from app.core.config import get_settings
from app.db.database import AsyncSessionLocal


async def check_db() -> bool:
    async with AsyncSessionLocal() as session:
        await session.execute(text("SELECT 1"))
    return True


async def check_redis() -> bool:
    import redis.asyncio as aioredis

    settings = get_settings()
    client = aioredis.from_url(settings.redis_url, decode_responses=True)
    try:
        return bool(await client.ping())
    finally:
        await client.aclose()


async def main(mode: str) -> int:
    try:
        if mode == "live":
            return 0
        if mode == "ready":
            await check_db()
            await check_redis()
            return 0
        if mode == "worker":
            await check_redis()
            return 0
        print(f"Unknown mode: {mode}", file=sys.stderr)
        return 1
    except Exception as exc:
        print(str(exc), file=sys.stderr)
        return 1


if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "ready"
    raise SystemExit(asyncio.run(main(mode)))
