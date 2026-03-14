from typing import Annotated

from fastapi import APIRouter, Depends, File, Path, UploadFile
from fastapi_exception_responses import Responses

from app.core.common.request_params import OrderingParamsDep, PaginationParamsDep
from app.core.common.responses import InvalidRequestParamsResponses, PaginatedResponse
from app.core.config import settings
from app.core.database.base_repository import InvalidOrderAttributeError
from app.core.utils.save_file import save_file
from app.domains.news.exceptions import NewsNotFoundError
from app.domains.news.filters import NewsFilter
from app.domains.news.models import CreateNewsSchema, NewsSchema, UpdateNewsSchema
from app.domains.news.services import NewsServiceDep
from app.domains.shared.deps import AdminUserDep

router = APIRouter(prefix="/news", tags=["News"])


@router.post("", summary="Create news")
async def create_news(
    body: CreateNewsSchema,
    admin: AdminUserDep,
    service: NewsServiceDep,
):
    news = await service.create_news(**body.model_dump(), author_id=admin.id)
    return news


class UploadImageResponses(Responses):
    INVALID_CONTENT_TYPE = 422, "Invalid image content type"


@router.post("/images", responses=UploadImageResponses.responses, summary="Upload image for a single news")
async def upload_image(
    file: Annotated[UploadFile, File(...)],
    admin: AdminUserDep,  # noqa
) -> dict:
    if not file.content_type.startswith("image/"):
        raise UploadImageResponses.INVALID_CONTENT_TYPE

    relative_filepath = await save_file(file, settings.NEWS_UPLOADS_PATH)

    return {"path": relative_filepath.as_posix()}


class NewsNotFoundResponses(Responses):
    NEWS_NOT_FOUND = 404, "News with provided id not found"


@router.put(
    "/{news_id}",
    summary="Update news by id",
    responses=NewsNotFoundResponses.responses,
)
async def update_news(
    news_id: Annotated[int, Path(...)],
    body: UpdateNewsSchema,
    admin: AdminUserDep,  # noqa
    service: NewsServiceDep,
) -> None:
    try:
        await service.update_news(news_id, body.model_dump())
    except NewsNotFoundError:
        raise NewsNotFoundResponses.NEWS_NOT_FOUND


@router.get(
    "",
    summary="Paginated, ordered, filtered list of news",
    responses=InvalidRequestParamsResponses.responses,
)
async def get_all_news(
    news_service: NewsServiceDep,
    params: PaginationParamsDep,
    ordering: OrderingParamsDep = None,
    filters: Annotated[NewsFilter, Depends()] = None,
) -> PaginatedResponse[NewsSchema]:
    try:
        news, news_count = await news_service.get_all_paginated_counted(
            order_by=ordering,
            filters=filters.model_dump(exclude_none=True),
            limit=params["limit"],
            offset=params["offset"],
        )
        data = [NewsSchema.from_orm(single_news) for single_news in news]
        return PaginatedResponse(
            count=news_count,
            data=data,
            page=params["page"],
            page_size=params["page_size"],
        )
    except InvalidOrderAttributeError:
        raise InvalidRequestParamsResponses.INVALID_SORTER_FIELD


@router.get("/{news_id}", summary="Returns single news by id", responses=NewsNotFoundResponses.responses)
async def get_news_detail(
    news_id: Annotated[int, Path(...)],
    news_service: NewsServiceDep,
) -> NewsSchema:
    try:
        news = await news_service.get_news_by_id(news_id)
        if news.is_deleted:
            raise NewsNotFoundResponses.NEWS_NOT_FOUND
        return NewsSchema.from_orm(news)
    except NewsNotFoundError:
        raise NewsNotFoundResponses.NEWS_NOT_FOUND


@router.delete("/{news_id}", summary="Deletes news by id", responses=NewsNotFoundResponses.responses)
async def delete_news(
    news_id: Annotated[int, Path(...)],
    news_service: NewsServiceDep,
):
    try:
        await news_service.set_news_deleted(news_id)
    except NewsNotFoundError:
        raise NewsNotFoundResponses.NEWS_NOT_FOUND
