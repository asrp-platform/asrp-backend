from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi_exception_responses import Responses

from app.core.common.request_params import OrderingParamsDep, PaginationParamsDep
from app.core.common.responses import PaginatedResponse
from app.domains.news.cache import NewsCacheDep, is_first_page
from app.domains.news.filters import PublicNewsFilter
from app.domains.news.schemas import NewsSchema
from app.domains.news.use_cases import GetNewsListUseCaseDep, GetPublishedNewsBySlugUseCaseDep


router = APIRouter(prefix="/news", tags=["News"])


class PublicNewsResponses(Responses):
    INVALID_FILTER_FIELD = 400, "Invalid filter field"
    INVALID_SORTER_FIELD = 400, "Invalid sorter field"


class PublicNewsDetailResponses(Responses):
    NEWS_NOT_FOUND = 404, "News with provided slug not found"


@router.get(
    "",
    summary="Get a paginated list of published news",
    responses=PublicNewsResponses.responses,
)
async def get_published_news_paginated_counted(
    use_case: GetNewsListUseCaseDep,
    params: PaginationParamsDep,
    cache: NewsCacheDep,
    ordering: OrderingParamsDep = None,
    filters: Annotated[PublicNewsFilter, Depends()] = None,
) -> PaginatedResponse[NewsSchema]:
    news_filters = filters.model_dump(exclude_none=True)
    use_cache = is_first_page(params=params, ordering=ordering, filters=news_filters)

    if use_cache:
        cached_data = await cache.get_first_page_from_cache()
        if cached_data is not None:
            return cached_data

    news_filters["is_published"] = True

    data, count = await use_case.execute(
        permissions=None,
        order_by=ordering,
        filters=news_filters,
        limit=params["limit"],
        offset=params["offset"],
    )
    response = PaginatedResponse[NewsSchema](
        count=count,
        data=data,
        page=params["page"],
        page_size=params["page_size"],
    )
    if use_cache:
        await cache.cache_first_page(response)
    return response


@router.get(
    "/{slug}",
    summary="Get published news by slug",
    responses=PublicNewsDetailResponses.responses,
)
async def get_published_news_detail(
    slug: str,
    use_case: GetPublishedNewsBySlugUseCaseDep,
) -> NewsSchema:
    return await use_case.execute(slug)
