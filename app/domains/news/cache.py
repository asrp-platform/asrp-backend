from typing import Annotated

from fastapi import Depends
from loguru import logger

from app.core.common.redis_client import RedisClientDep
from app.core.common.request_params import OrderingParamsDep, PaginationParamsDep
from app.core.common.responses import PaginatedResponse
from app.domains.news.schemas import NewsSchema


def is_first_page(
    *,
    params: PaginationParamsDep,
    ordering: OrderingParamsDep = None,
    filters: dict,
) -> bool:
    return params["offset"] == 0 and ordering == "-created_at" and not filters


class NewsCache:
    FIRST_PAGE_CACHE_TTL_SECONDS = 300
    FIRST_PAGE_CACHE_KEY = "news:list:v1:page=1:size=8:ordering=-created_at"

    def __init__(self, redis_client: RedisClientDep):
        self._redis = redis_client

    async def cache_first_page(self, response: PaginatedResponse[NewsSchema]) -> None:
        try:
            await self._redis.set(
                self.FIRST_PAGE_CACHE_KEY,
                response.model_dump_json(),
                ex=self.FIRST_PAGE_CACHE_TTL_SECONDS,
            )
        except (ConnectionError, TimeoutError) as error:
            logger.error("Redis connection error. Error = {}", error)

    async def get_first_page_from_cache(self) -> PaginatedResponse[NewsSchema] | None:
        try:
            cached_value = await self._redis.get(self.FIRST_PAGE_CACHE_KEY)
        except (ConnectionError, TimeoutError) as error:
            logger.error("Redis connection error. Error = {}", error)
            return None

        if cached_value is None:
            return None

        try:
            return PaginatedResponse[NewsSchema].model_validate_json(cached_value)
        except ValueError:
            logger.exception("Invalid news first page found in cache")
            await self.invalidate_first_page()
            return None

    async def invalidate_first_page(self) -> None:
        try:
            await self._redis.delete(self.FIRST_PAGE_CACHE_KEY)
        except (ConnectionError, TimeoutError) as error:
            logger.error("Unable to invalidate news cache. Error = {}", error)


NewsCacheDep = Annotated[NewsCache, Depends()]
