from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi.params import Path

from app.core.common.request_params import OrderingParamsDep, PaginationParamsDep
from app.core.common.responses import (
    InvalidRequestParamsResponses,
    NotAuthorizedResponses,
    PaginatedResponse,
    PermissionsResponses,
)
from app.domains.permissions.models import PermissionSchema
from app.domains.permissions.services import PermissionServiceDep
from app.domains.shared.deps import AdminPermissionsDep, AdminUserDep, get_admin_user
from app.domains.users.filters import NameChangeRequestsFilters, UsersFilter
from app.domains.users.schemas import (
    BanUserSchema,
    NameChangeRequestUpdateByAdminSchema,
    NameChangeRequestViewSchema,
    UpdateUserByAdminSchema,
    UserPrivateSchema,
)
from app.domains.users.services import NameChangeRequestServiceDep
from app.domains.users.use_cases.ban_user import BanUserUseCaseDep
from app.domains.users.use_cases.unban_user import UnbanUserUseCaseDep
from app.domains.users.use_cases.update_user_by_admin import UpdateUserByAdminUseCaseDep
from app.domains.users.use_cases.users_admin.get_user_by_id import GetUserByIdUseCaseDep
from app.domains.users.use_cases.users_admin.get_users import GetUsersUseCaseDep


router = APIRouter(tags=["Admin: Users"], prefix="/users", dependencies=[Depends(get_admin_user)])


class UserListResponses(InvalidRequestParamsResponses, PermissionsResponses, NotAuthorizedResponses):
    pass


@router.get("", responses=UserListResponses.responses)
async def get_users(
    permissions: AdminPermissionsDep,
    use_case: GetUsersUseCaseDep,
    params: PaginationParamsDep,
    ordering: OrderingParamsDep = None,
    filters: Annotated[UsersFilter, Depends()] = None,
) -> PaginatedResponse[UserPrivateSchema]:
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


class NameChangeRequestResponses(InvalidRequestParamsResponses, PermissionsResponses):
    USER_NOT_FOUND = 404, "User with provided ID not found"
    NAME_CHANGE_REQUEST_NOT_FOUND = 404, "Name change request with provided ID not found"
    PENDING_NAME_CHANGE_REQUEST_ALREADY_EXISTS = 409, "Pending name change request already exists"
    FIELD_REASON_REJECTING_IS_REQUIRED = 422, "Specifying the reason for rejecting the request is mandatory"
    NAME_CHANGE_REQUEST_COOLDOWN_NOT_EXPIRED = 429, "Name change request cooldown not expired"


@router.get(
    "/name-change-requests",
    responses=NameChangeRequestResponses.responses,
    summary="Get a list of name change requests",
)
async def get_name_change_requests(
    permissions: AdminPermissionsDep,
    service: NameChangeRequestServiceDep,
    params: PaginationParamsDep,
    ordering: OrderingParamsDep = None,
    filters: Annotated[NameChangeRequestsFilters, Depends()] = None,
) -> PaginatedResponse[NameChangeRequestViewSchema]:
    if "name_change_requests.view" not in permissions:
        raise NameChangeRequestResponses.PERMISSION_ERROR

    data, count = await service.get_all_paginated_counted_name_change_requests(
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


@router.get("/{user_id}")
async def get_user_by_admin(
    user_id: int,
    permissions: AdminPermissionsDep,
    use_case: GetUserByIdUseCaseDep,
) -> UserPrivateSchema:
    return await use_case.execute(permissions, user_id)


class UpdateUserByAdminResponses(PermissionsResponses):
    USER_NOT_FOUND = 404, "User with provided ID not found"


@router.patch(
    "/{user_id}",
    responses=UpdateUserByAdminResponses.responses,
    summary="Update user profile data by admin",
)
async def update_user_by_admin(
    user_id: Annotated[int, Path()],
    admin: AdminUserDep,
    permissions: AdminPermissionsDep,
    update_data: UpdateUserByAdminSchema,
    use_case: UpdateUserByAdminUseCaseDep,
):
    return await use_case.execute(
        target_user_id=user_id,
        admin=admin,
        permissions=permissions,
        update_data=update_data.model_dump(exclude_unset=True),
    )


class GetPermissionsResponses(PermissionsResponses):
    USER_NOT_FOUND = 404, "User with provided ID not found"


@router.get(
    "/{user_id}/permissions",
    responses=GetPermissionsResponses.responses,
    summary="Get user permissions",
)
async def get_user_permissions(
    user_id: Annotated[int, Path()],
    permissions_service: PermissionServiceDep,
    current_user_permissions: AdminPermissionsDep,
) -> list[PermissionSchema]:
    if "permissions.view" not in current_user_permissions:
        raise GetPermissionsResponses.PERMISSION_ERROR
    return await permissions_service.get_user_permissions(user_id)


class ManagePermissionsResponses(PermissionsResponses):
    USER_NOT_FOUND = 404, "User with provided ID not found"


@router.put("/{user_id}/permissions", responses=ManagePermissionsResponses.responses, summary="Set user permissions")
async def set_user_permissions(
    user_id: Annotated[int, Path()],
    permissions_service: PermissionServiceDep,
    current_user_permissions: AdminPermissionsDep,
    admin: AdminUserDep,
    permissions_ids: list[int],
):
    if "permissions.update" not in current_user_permissions:
        raise ManagePermissionsResponses.PERMISSION_ERROR

    return await permissions_service.set_users_permissions(user_id, permissions_ids, admin)


@router.get(
    "/{user_id}/name-change-requests/{name_change_request_id}",
    responses=NameChangeRequestResponses.responses,
    summary="Get request for a firstname and lastname change",
)
async def get_pending_name_change_request(
    user_id: Annotated[int, Path()],
    name_change_request_id: Annotated[int, Path()],
    permissions: AdminPermissionsDep,
    service: NameChangeRequestServiceDep,
) -> NameChangeRequestViewSchema:
    if "name_change_requests.view" not in permissions:
        raise NameChangeRequestResponses.PERMISSION_ERROR

    return await service.get_pending_name_change_request(user_id, name_change_request_id)


@router.patch(
    "/{user_id}/name-change-requests/{name_change_request_id}",
    status_code=204,
    responses=NameChangeRequestResponses.responses,
    summary="Approve/reject a firstname and lastname change request",
)
async def update_name_change_request(
    user_id: Annotated[int, Path()],
    name_change_request_id: Annotated[int, Path()],
    name_change_request_data: NameChangeRequestUpdateByAdminSchema,
    permissions: AdminPermissionsDep,
    service: NameChangeRequestServiceDep,
) -> None:
    await service._update_name_change_request(  # noqa intensional direct call from service
        permissions,
        user_id,
        name_change_request_id,
        name_change_request_data.action,
        name_change_request_data.reason_rejecting,
    )


class BanUserResponses(PermissionsResponses):
    USER_NOT_FOUND = 404, "User with provided ID not found"


@router.patch(
    "/{user_id}/ban",
    responses=BanUserResponses.responses,
    summary="Ban a user",
)
async def ban_user(
    user_id: Annotated[int, Path()],
    ban_data: BanUserSchema,
    admin: AdminUserDep,
    permissions: AdminPermissionsDep,
    use_case: BanUserUseCaseDep,
) -> UserPrivateSchema:
    return await use_case.execute(
        target_user_id=user_id, admin=admin, permissions=permissions, ban_reason=ban_data.ban_reason
    )


@router.delete(
    "/{user_id}/ban",
    responses=BanUserResponses.responses,
    summary="Unban a user",
)
async def unban_user(
    user_id: Annotated[int, Path()],
    admin: AdminUserDep,
    permissions: AdminPermissionsDep,
    use_case: UnbanUserUseCaseDep,
) -> UserPrivateSchema:
    return await use_case.execute(
        target_user_id=user_id,
        admin=admin,
        permissions=permissions,
    )
