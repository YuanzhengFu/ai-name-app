import redis.asyncio as redis
from typing import AsyncGenerator
from settings import REDIS_URL

redis_client = redis.from_url(REDIS_URL,encoding="utf-8",decode_responses=True)


async def get_redis_client() -> AsyncGenerator[redis.Redis,None]:
    yield redis_client
