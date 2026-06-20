import redis.asyncio as redis
from typing import AsyncGenerator

url = "redis://127.0.0.1:6379/0"
redis_client = redis.from_url(url,encoding="utf-8",decode_responses=True)


async def get_redis_client() -> AsyncGenerator[redis.Redis,None]:
    yield redis_client