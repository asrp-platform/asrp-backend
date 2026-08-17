from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi_exception_responses import Responses

from app.core.common.request_params import OrderingParamsDep, PaginationParamsDep
from app.core.common.responses import PaginatedResponse
from app.domains.news.filters import PublicNewsFilter
from app.domains.news.schemas import NewsSchema
from app.domains.news.services import NewsServiceDep


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
    service: NewsServiceDep,
    params: PaginationParamsDep,
    ordering: OrderingParamsDep = None,
    filters: Annotated[PublicNewsFilter, Depends()] = None,
) -> PaginatedResponse[NewsSchema]:
    news_filters = filters.model_dump(exclude_none=True)
    news_filters["is_published"] = True
    data, count = await service.get_news_paginated_counted(
        order_by=ordering,
        filters=news_filters,
        limit=params["limit"],
        offset=params["offset"],
        open_transaction=True,
    )
    return PaginatedResponse(
        count=count,
        data=data,
        page=params["page"],
        page_size=params["page_size"],
    )


@router.get(
    "/{slug}",
    summary="Get published news by slug",
    responses=PublicNewsDetailResponses.responses,
)
async def get_published_news_detail(
    slug: str,
    service: NewsServiceDep,
) -> NewsSchema:
    return await service.get_published_news_by_slug(slug)
