from typing import Annotated, Any, Mapping

from fastapi import Depends
from loguru import logger
from pydantic import ValidationError
from redis.exceptions import ConnectionError as RedisConnectionError, TimeoutError as RedisTimeoutError

from app.core.common.redis_client import RedisClientDep
from app.core.common.responses import PaginatedResponse
from app.domains.news.schemas import NewsSchema


FIRST_PAGE_SIZE = 8
FIRST_PAGE_ORDERING = "-created_at"


def is_first_page(
    *,
    params: Mapping[str, int],
    ordering: str | None,
    filters: Mapping[str, Any],
) -> bool:
    return (
        params["page"] == 1
        and params["page_size"] == FIRST_PAGE_SIZE
        and ordering == FIRST_PAGE_ORDERING
        and not filters
    )


class NewsCache:
    FIRST_PAGE_CACHE_TTL_SECONDS = 300
    FIRST_PAGE_CACHE_KEY = f"news:list:v1:page=1:size={FIRST_PAGE_SIZE}:ordering={FIRST_PAGE_ORDERING}"

    def __init__(self, redis_client: RedisClientDep):
        self._redis = redis_client

    async def cache_first_page(self, response: PaginatedResponse[NewsSchema]) -> None:
        try:
            await self._redis.set(
                self.FIRST_PAGE_CACHE_KEY,
                response.model_dump_json(),
                ex=self.FIRST_PAGE_CACHE_TTL_SECONDS,
            )
        except (RedisConnectionError, RedisTimeoutError) as error:
            logger.warning("Unable to cache the first news page: {}", error)

    async def get_first_page_from_cache(self) -> PaginatedResponse[NewsSchema] | None:
        try:
            cached_value = await self._redis.get(self.FIRST_PAGE_CACHE_KEY)
        except (RedisConnectionError, RedisTimeoutError) as error:
            logger.warning("Unable to read the first news page cache: {}", error)
            return None

        if cached_value is None:
            return None

        try:
            return PaginatedResponse[NewsSchema].model_validate_json(cached_value)
        except ValidationError:
            logger.exception("Invalid news first page found in cache")
            await self.invalidate_first_page()
            return None

    async def invalidate_first_page(self) -> None:
        try:
            await self._redis.delete(self.FIRST_PAGE_CACHE_KEY)
        except (RedisConnectionError, RedisTimeoutError) as error:
            logger.warning("Unable to invalidate the first news page cache: {}", error)


NewsCacheDep = Annotated[NewsCache, Depends()]
