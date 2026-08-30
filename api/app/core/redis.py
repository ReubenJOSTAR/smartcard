"""Redis connection pool — OTP storage only in MVP."""

from redis.asyncio import Redis

from app.core.config import settings

redis_pool: Redis = Redis.from_url(settings.REDIS_URL, decode_responses=True)


async def get_redis() -> Redis:
    return redis_pool
