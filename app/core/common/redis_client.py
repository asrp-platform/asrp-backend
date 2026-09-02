from typing import Annotated

from fastapi import Depends
from redis.asyncio import Redis
from redis.backoff import NoBackoff
from redis.client import Retry

from app.core.config import settings


redis_client = Redis(
    host=settings.REDIS_HOST,
    port=settings.REDIS_PORT,
    username=settings.REDIS_USER,
    password=settings.REDIS_USER_PASSWORD,
    db=settings.REDIS_DB_NUMBER,
    socket_timeout=settings.REDIS_SOCKET_TIMEOUT,
    decode_responses=True,
    retry=Retry(backoff=NoBackoff(), retries=0),
)


def get_redis_client() -> Redis:
    return redis_client


RedisClientDep = Annotated[Redis, Depends(get_redis_client)]
