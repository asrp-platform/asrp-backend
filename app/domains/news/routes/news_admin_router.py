from typing import Annotated

from fastapi import APIRouter, Depends, File, UploadFile
from fastapi_exception_responses import Responses

from app.core.common.request_params import OrderingParamsDep, PaginationParamsDep
from app.core.common.responses import PaginatedResponse
from app.core.utils.permissions import check_permissions
from app.domains.news.filters import NewsFilter
from app.domains.news.schemas import CreateNewsSchema, NewsSchema, UpdateNewsSchema
from app.domains.news.services import NewsServiceDep
from app.domains.shared.deps import AdminPermissionsDep, AdminUserDep, get_admin_user
from app.domains.shared.schemas import UploadedImageSchema
from app.domains.shared.types import FileData


router = APIRouter(
    prefix="/news",
    tags=["Admin: News"],
    dependencies=[Depends(get_admin_user)],
)


class AdminNewsResponses(Responses):
    NOT_AUTHORIZED = 401, "Not authorized"
    PERMISSION_ERROR = 403, "Not enough permissions"


class NewsListResponses(AdminNewsResponses):
    INVALID_FILTER_FIELD = 400, "Invalid filter field"
    INVALID_SORTER_FIELD = 400, "Invalid sorter field"


class NewsDetailResponses(AdminNewsResponses):
    NEWS_NOT_FOUND = 404, "News with provided ID not found"


class UploadNewsImageResponses(AdminNewsResponses):
    INVALID_CONTENT_TYPE = 415, "Invalid image content type"


@router.get(
    "",
    summary="Get a paginated list of news",
    responses=NewsListResponses.responses,
)
async def get_news_paginated_counted(
    permissions: AdminPermissionsDep,
    service: NewsServiceDep,
    params: PaginationParamsDep,
    ordering: OrderingParamsDep = None,
    filters: Annotated[NewsFilter, Depends()] = None,
) -> PaginatedResponse[NewsSchema]:
    check_permissions("news.view", permissions)
    data, count = await service.get_news_paginated_counted(
        order_by=ordering,
        filters=filters.model_dump(exclude_none=True),
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


@router.post(
    "",
    status_code=201,
    summary="Create news",
    responses=AdminNewsResponses.responses,
)
async def create_news(
    permissions: AdminPermissionsDep,
    current_user: AdminUserDep,
    service: NewsServiceDep,
    body: CreateNewsSchema,
) -> NewsSchema:
    check_permissions("news.create", permissions)
    return await service.create_news(**body.model_dump(), author_id=current_user.id)


@router.post(
    "/images",
    status_code=201,
    summary="Upload a news image",
    responses=UploadNewsImageResponses.responses,
)
async def upload_image(
    file: Annotated[UploadFile, File(...)],
    permissions: AdminPermissionsDep,
    service: NewsServiceDep,
) -> UploadedImageSchema:
    check_permissions("news.create", permissions)
    file_data = FileData(
        content=await file.read(),
        content_type=file.content_type,
        filename=file.filename,
    )
    file_path = await service.upload_image(file_data)
    return UploadedImageSchema(path=file_path)


@router.get(
    "/{news_id}",
    summary="Get news by ID",
    responses=NewsDetailResponses.responses,
)
async def get_news_detail(
    news_id: int,
    permissions: AdminPermissionsDep,
    service: NewsServiceDep,
) -> NewsSchema:
    check_permissions("news.view", permissions)
    return await service.get_news_by_id(news_id)


@router.patch(
    "/{news_id}",
    summary="Update news by ID",
    responses=NewsDetailResponses.responses,
)
async def update_news(
    news_id: int,
    permissions: AdminPermissionsDep,
    service: NewsServiceDep,
    body: UpdateNewsSchema,
) -> NewsSchema:
    check_permissions("news.update", permissions)
    return await service.update_news(news_id, body.model_dump(exclude_unset=True))


@router.delete(
    "/{news_id}",
    status_code=204,
    summary="Delete news by ID",
    responses=NewsDetailResponses.responses,
)
async def delete_news(
    news_id: int,
    permissions: AdminPermissionsDep,
    service: NewsServiceDep,
) -> None:
    check_permissions("news.delete", permissions)
    await service.delete_news_by_id(news_id)
