"""Redis connection pool — OTP storage only in MVP. Placeholder.
See progress.md → Backend — Core → "Redis connection pool — OTP only".
"""

from redis.asyncio import Redis

redis_pool: Redis


async def get_redis() -> Redis:
    ...
