import pytest

import redis.asyncio
from redisdb.interface import RedisDB


@pytest.fixture
async def redis_client():
    async with redis.asyncio.Redis(db=7) as redis_client:
        yield redis_client

        await redis_client.flushdb()


@pytest.fixture
def db(redis_client):
    return RedisDB(redis_client)
