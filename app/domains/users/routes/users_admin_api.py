from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi.params import Path
from fastapi_exception_responses import Responses

from app.core.common.request_params import OrderingParamsDep, PaginationParamsDep
from app.core.common.responses import InvalidRequestParamsResponses, PaginatedResponse, PermissionsResponses
from app.core.database.base_repository import InvalidOrderAttributeError
from app.domains.permissions.models import PermissionSchema
from app.domains.permissions.services import PermissionServiceDep
from app.domains.shared.deps import AdminPermissionsDep, AdminUserDep, get_admin_user
from app.domains.users.filters import NameChangeRequestsFilters, UsersFilter
from app.domains.users.schemas import (
    BanUserSchema,
    NameChangeRequestUpdateByAdminSchema,
    NameChangeRequestViewSchema,
    UpdateUserByAdminSchema,
    UserSchema,
)
from app.domains.users.services import NameChangeRequestServiceDep, UserServiceDep


router = APIRouter(tags=["Admin: Users"], prefix="/users", dependencies=[Depends(get_admin_user)])


class UserListResponses(InvalidRequestParamsResponses):
    PERMISSION_ERROR = 403, "Don't have enough permissions"


@router.get("", responses=UserListResponses.responses)
async def get_users(
    user_service: UserServiceDep,
    params: PaginationParamsDep,
    permissions: AdminPermissionsDep,
    ordering: OrderingParamsDep = None,
    filters: Annotated[UsersFilter, Depends()] = None,
) -> PaginatedResponse[UserSchema]:
    if "users.view" not in permissions:
        raise UserListResponses.PERMISSION_ERROR
    try:
        users, users_count = await user_service.get_all_paginated_counted(
            order_by=ordering,
            filters=filters.model_dump(exclude_none=True),
            limit=params["limit"],
            offset=params["offset"],
        )
        data = [UserSchema.from_orm(user) for user in users]
        return PaginatedResponse(
            count=users_count,
            data=data,
            page=params["page"],
            page_size=params["page_size"],
        )
    except InvalidOrderAttributeError:
        raise UserListResponses.INVALID_SORTER_FIELD


class NameChangeRequestResponses(InvalidRequestParamsResponses):
    PERMISSION_ERROR = 403, "Don't have enough permissions to view name change requests"
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

    try:
        name_change_requests, count = await service.get_all_paginated_counted_name_change_requests(
            order_by=ordering,
            filters=filters.model_dump(exclude_none=True),
            limit=params["limit"],
            offset=params["offset"],
        )
        data = [NameChangeRequestViewSchema.model_validate(request) for request in name_change_requests]
        return PaginatedResponse(
            count=count,
            data=data,
            page=params["page"],
            page_size=params["page_size"],
        )
    except InvalidOrderAttributeError:
        raise NameChangeRequestResponses.INVALID_SORTER_FIELD


class UpdateUserByAdminResponses(Responses):
    CANT_GRANT_ADMIN_ROLE = 403, "Don't have enough permissions to grand admin role"
    CANT_REVOKE_ADMIN_ROLE = 403, "Don't have enough permissions to revoke admin role"
    USER_NOT_FOUND = 404, "User with provided ID not found"
    PERMISSION_ERROR = 403, "Don't have enough permissions"


@router.patch(
    "/{user_id}",
    responses=UpdateUserByAdminResponses.responses,
    summary="Update user profile data by admin",
)
async def update_user_by_admin(
    user_id: Annotated[int, Path()],
    user_service: UserServiceDep,
    admin: AdminUserDep,
    permissions: AdminPermissionsDep,
    update_data: UpdateUserByAdminSchema,
):
    target_user = await user_service.get_user_by_kwargs(id=user_id)
    if target_user is None:
        raise UpdateUserByAdminResponses.USER_NOT_FOUND

    if target_user.admin:
        if "admin.update" not in permissions:
            raise UpdateUserByAdminResponses.PERMISSION_ERROR
    else:
        if "users.update" not in permissions:
            raise UpdateUserByAdminResponses.PERMISSION_ERROR

    if update_data.admin is True and "admin.create" not in permissions:
        raise UpdateUserByAdminResponses.CANT_GRANT_ADMIN_ROLE
    if update_data.admin is not True and "admin.delete" not in permissions:
        raise UpdateUserByAdminResponses.CANT_REVOKE_ADMIN_ROLE
    if update_data.admin and admin.id == user_id:
        raise UpdateUserByAdminResponses.CANT_REVOKE_ADMIN_ROLE

    return await user_service.update_user(user_id, **update_data.model_dump(exclude_unset=True))


class GetPermissionsResponses(PermissionsResponses):
    PERMISSION_ERROR = 403, "Don't have enough permissions to read user permissions"
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
    PERMISSION_ERROR = 403, "Don't have enough permissions to manage user permissions"
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
    if "name_change_requests.update" not in permissions:
        raise NameChangeRequestResponses.PERMISSION_ERROR

    await service.update_name_change_request(
        user_id, name_change_request_id, name_change_request_data.action, name_change_request_data.reason_rejecting
    )


class BanUserResponses(Responses):
    USER_NOT_FOUND = 404, "User with provided ID not found"
    CANT_BAN_SELF = 400, "You cannot ban yourself"
    CANT_UNBAN_SELF = 400, "You cannot unban yourself"
    CANT_BAN_SUPERADMIN = 403, "You cannot ban the system administrator"
    PERMISSION_ERROR = 403, "Don't have enough permissions"


@router.put(
    "/{user_id}/ban",
    responses=BanUserResponses.responses,
    summary="Ban a user",
)
async def ban_user(
    user_id: Annotated[int, Path()],
    ban_data: BanUserSchema,
    user_service: UserServiceDep,
    admin: AdminUserDep,
    permissions: AdminPermissionsDep,
) -> UserSchema:
    if admin.id == user_id:
        raise BanUserResponses.CANT_BAN_SELF

    target_user = await user_service.get_user_by_kwargs(id=user_id)
    if target_user is None:
        raise BanUserResponses.USER_NOT_FOUND

    if target_user.superuser:
        raise BanUserResponses.CANT_BAN_SUPERADMIN

    if target_user.admin:
        if "admin.update" not in permissions:
            raise BanUserResponses.PERMISSION_ERROR
    else:
        if "users.update" not in permissions:
            raise BanUserResponses.PERMISSION_ERROR

    user = await user_service.ban_user(user_id, ban_data.ban_reason)
    return UserSchema.model_validate(user)


@router.delete(
    "/{user_id}/ban",
    responses=BanUserResponses.responses,
    summary="Unban a user",
)
async def unban_user(
    user_id: Annotated[int, Path()],
    user_service: UserServiceDep,
    admin: AdminUserDep,
    permissions: AdminPermissionsDep,
) -> UserSchema:
    if admin.id == user_id:
        raise BanUserResponses.CANT_UNBAN_SELF

    target_user = await user_service.get_user_by_kwargs(id=user_id)
    if target_user is None:
        raise BanUserResponses.USER_NOT_FOUND

    if target_user.superuser:
        raise BanUserResponses.PERMISSION_ERROR

    if target_user.admin:
        if "admin.update" not in permissions:
            raise BanUserResponses.PERMISSION_ERROR
    else:
        if "users.update" not in permissions:
            raise BanUserResponses.PERMISSION_ERROR

    user = await user_service.unban_user(user_id)
    return UserSchema.model_validate(user)
