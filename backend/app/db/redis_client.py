import redis.asyncio as redis

from app.core.settings import settings

redis_client = redis.from_url(
    settings.redis_settings.REDIS_URL, encoding="utf-8", decode_responses=True
)


async def set_cache(key: str, value: str, expire: int = 60):
    await redis_client.set(key, value, ex=expire)


async def get_cache(key: str):
    return await redis_client.get(key)