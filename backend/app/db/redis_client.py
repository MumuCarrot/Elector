import redis.asyncio as redis

from app.core.settings import settings

redis_client = redis.from_url(
    settings.redis_settings.REDIS_URL, encoding="utf-8", decode_responses=True
)


async def set_cache(key: str, value: str, expire: int = 60) -> None:
    """Stores a string value in Redis with TTL.

    Args:
        key: Cache key.
        value: String payload.
        expire: Time-to-live in seconds.

    """
    await redis_client.set(key, value, ex=expire)


async def get_cache(key: str) -> str | None:
    """Reads a string value by key.

    Args:
        key: Cache key.

    Returns:
        Stored value or None if missing.

    """
    return await redis_client.get(key)
