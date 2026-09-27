from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi_exception_responses import Responses

from app.core.common.request_params import OrderingParamsDep, PaginationParamsDep
from app.core.common.responses import PaginatedResponse
from app.domains.news.filters import WebinarFilters
from app.domains.news.schemas import CreateWebinarSchema, UpdateWebinarSchema, WebinarBaseSchema
from app.domains.news.use_cases import (
    CreateWebinarUseCaseDep,
    DeleteWebinarUseCaseDep,
    GetAdminWebinarsUseCaseDep,
    GetRegisteredWebinarUsersUseCaseDep,
    GetWebinarUseCaseDep,
    UpdateWebinarUseCaseDep,
)
from app.domains.shared.deps import AdminPermissionsDep, get_admin_user
from app.domains.users.schemas import UserPrivateSchema


router = APIRouter(
    prefix="/webinars",
    tags=["Admin: Webinars"],
    dependencies=[Depends(get_admin_user)],
)


class AdminWebinarResponses(Responses):
    NOT_AUTHORIZED = 401, "Not authorized"
    PERMISSION_ERROR = 403, "Not enough permissions"


@router.get("", responses=AdminWebinarResponses.responses)
async def get_webinars_paginated_counted(
    permissions: AdminPermissionsDep,
    use_case: GetAdminWebinarsUseCaseDep,
    params: PaginationParamsDep,
    ordering: OrderingParamsDep = None,
    filters: Annotated[WebinarFilters, Depends()] = None,
) -> PaginatedResponse[WebinarBaseSchema]:
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


@router.post("", responses=AdminWebinarResponses.responses)
async def create_webinar(
    permissions: AdminPermissionsDep,
    use_case: CreateWebinarUseCaseDep,
    body: CreateWebinarSchema,
) -> WebinarBaseSchema:
    return await use_case.execute(permissions, body.model_dump())


class UpdateWebinarResponses(AdminWebinarResponses):
    WEBINAR_NOT_FOUND = 404, "Webinar with provided ID not found"


@router.get(
    "/{webinar_id}",
    responses=UpdateWebinarResponses.responses,
)
async def get_webinar(
    webinar_id: int,
    permissions: AdminPermissionsDep,
    use_case: GetWebinarUseCaseDep,
) -> WebinarBaseSchema:
    return await use_case.execute(permissions, webinar_id)


@router.patch(
    "/{webinar_id}",
    responses=UpdateWebinarResponses.responses,
)
async def update_webinar(
    webinar_id: int,
    permissions: AdminPermissionsDep,
    use_case: UpdateWebinarUseCaseDep,
    body: UpdateWebinarSchema,
) -> WebinarBaseSchema:
    return await use_case.execute(permissions, webinar_id, body.model_dump(exclude_unset=True))


class DeleteWebinarResponses(AdminWebinarResponses):
    WEBINAR_NOT_FOUND = 404, "Webinar with provided ID not found"


@router.delete(
    "/{webinar_id}",
    responses=DeleteWebinarResponses.responses,
    summary="Delete webinar by ID",
)
async def delete_webinar(
    webinar_id: int,
    permissions: AdminPermissionsDep,
    use_case: DeleteWebinarUseCaseDep,
) -> int:
    return await use_case.execute(permissions, webinar_id)


class RegisteredWebinarUsersResponses(AdminWebinarResponses):
    WEBINAR_NOT_FOUND = 404, "Webinar with provided ID not found"


@router.get(
    "/{webinar_id}/registrations",
    responses=RegisteredWebinarUsersResponses.responses,
    summary="Get users registered for a webinar",
)
async def get_webinar_registered_users(
    webinar_id: int,
    permissions: AdminPermissionsDep,
    use_case: GetRegisteredWebinarUsersUseCaseDep,
    params: PaginationParamsDep,
    ordering: OrderingParamsDep = None,
) -> PaginatedResponse[UserPrivateSchema]:
    data, count = await use_case.execute(
        permissions,
        webinar_id,
        limit=params["limit"],
        offset=params["offset"],
        order_by=ordering,
    )
    return PaginatedResponse(
        count=count,
        data=data,
        page=params["page"],
        page_size=params["page_size"],
    )
