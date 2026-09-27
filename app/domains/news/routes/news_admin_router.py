from typing import Annotated

from fastapi import APIRouter, Depends, File, UploadFile
from fastapi_exception_responses import Responses

from app.core.common.request_params import OrderingParamsDep, PaginationParamsDep
from app.core.common.responses import PaginatedResponse
from app.domains.news.filters import NewsFilter
from app.domains.news.schemas import CreateNewsSchema, NewsSchema, UpdateNewsSchema
from app.domains.news.use_cases import (
    CreateNewsUseCaseDep,
    DeleteNewsUseCaseDep,
    GetNewsByIdUseCaseDep,
    GetNewsListUseCaseDep,
    UpdateNewsUseCaseDep,
    UploadNewsImageUseCaseDep,
)
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
    FILE_TOO_LARGE = 413, "Image must be smaller than 5 MB"
    INVALID_CONTENT_TYPE = 415, "Invalid image content type"


@router.get(
    "",
    summary="Get a paginated list of news",
    responses=NewsListResponses.responses,
)
async def get_news_paginated_counted(
    permissions: AdminPermissionsDep,
    use_case: GetNewsListUseCaseDep,
    params: PaginationParamsDep,
    ordering: OrderingParamsDep = None,
    filters: Annotated[NewsFilter, Depends()] = None,
) -> PaginatedResponse[NewsSchema]:
    data, count = await use_case.execute(
        permissions,
        order_by=ordering,
        filters=filters.model_dump(exclude_none=True),
        limit=params["limit"],
        offset=params["offset"],
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
    use_case: CreateNewsUseCaseDep,
    body: CreateNewsSchema,
) -> NewsSchema:
    return await use_case.execute(permissions, current_user.id, body.model_dump())


@router.post(
    "/images",
    status_code=201,
    summary="Upload a news image",
    responses=UploadNewsImageResponses.responses,
)
async def upload_image(
    file: Annotated[UploadFile, File(...)],
    permissions: AdminPermissionsDep,
    use_case: UploadNewsImageUseCaseDep,
) -> UploadedImageSchema:
    file_data = FileData(
        content=await file.read(),
        content_type=file.content_type,
        filename=file.filename,
    )
    stored_file = await use_case.execute(permissions, file_data)
    return UploadedImageSchema(
        file_url=stored_file.file_url,
        object_key=stored_file.object_key,
    )


@router.get(
    "/{news_id}",
    summary="Get news by ID",
    responses=NewsDetailResponses.responses,
)
async def get_news_detail(
    news_id: int,
    permissions: AdminPermissionsDep,
    use_case: GetNewsByIdUseCaseDep,
) -> NewsSchema:
    return await use_case.execute(permissions, news_id)


@router.patch(
    "/{news_id}",
    summary="Update news by ID",
    responses=NewsDetailResponses.responses,
)
async def update_news(
    news_id: int,
    permissions: AdminPermissionsDep,
    use_case: UpdateNewsUseCaseDep,
    body: UpdateNewsSchema,
) -> NewsSchema:
    return await use_case.execute(permissions, news_id, body.model_dump(exclude_unset=True))


@router.delete(
    "/{news_id}",
    status_code=204,
    summary="Delete news by ID",
    responses=NewsDetailResponses.responses,
)
async def delete_news(
    news_id: int,
    permissions: AdminPermissionsDep,
    use_case: DeleteNewsUseCaseDep,
) -> None:
    await use_case.execute(permissions, news_id)
