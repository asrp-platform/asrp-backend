from datetime import datetime, timezone
from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi.params import Path
from fastapi_exception_responses import Responses

from app.core.common.request_params import OrderingParamsDep, PaginationParamsDep
from app.core.common.responses import InvalidRequestParamsResponses, PaginatedResponse, PermissionsResponses
from app.core.database.base_repository import InvalidOrderAttributeError
from app.domains.permissions.models import PermissionSchema
from app.domains.permissions.services import PermissionServiceDep
from app.domains.shared.deps import AdminPermissionsDep, AdminUserDep
from app.domains.users.exceptions import UserNotFoundError
from app.domains.users.filters import UsersFilter
from app.domains.users.schemas import UpdateUserByAdminSchema, UserSchema
from app.domains.users.services import UserServiceDep

router = APIRouter(tags=["Admin: Users"], prefix="/users")


class UserListResponses(InvalidRequestParamsResponses):
    pass


@router.get("", responses=UserListResponses.responses)
async def get_users(
    user_service: UserServiceDep,
    params: PaginationParamsDep,
    admin: AdminUserDep,  # noqa Admin auth argument
    ordering: OrderingParamsDep = None,
    filters: Annotated[UsersFilter, Depends()] = None,
) -> PaginatedResponse[UserSchema]:
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


class UpdateUserByAdminResponses(Responses):
    CANT_GRANT_ADMIN_ROLE = 403, "Don't have enough permissions to grand admin role"
    CANT_REVOKE_ADMIN_ROLE = 403, "Don't have enough permissions to revoke admin role"
    USER_NOT_FOUND = 404, "User with provided ID not found"


@router.patch(
    "/{user_id}",
    responses=UpdateUserByAdminResponses.responses,
    summary="Update user profile data by admin",
)
async def update_user_by_admin(
    user_id: Annotated[int, Path()],
    user_service: UserServiceDep,
    admin: AdminUserDep,  # noqa Admin auth argument
    permissions: AdminPermissionsDep,
    update_data: UpdateUserByAdminSchema,
):
    if update_data.stuff is True and "admin.create" not in permissions:
        raise UpdateUserByAdminResponses.CANT_GRANT_ADMIN_ROLE
    if update_data.stuff is not True and "admin.delete" not in permissions:
        raise UpdateUserByAdminResponses.CANT_REVOKE_ADMIN_ROLE
    if update_data.stuff and admin.id == user_id:
        raise UpdateUserByAdminResponses.CANT_REVOKE_ADMIN_ROLE

    try:
        return await user_service.update_user(user_id, update_data.model_dump())
    except UserNotFoundError:
        raise UpdateUserByAdminResponses.USER_NOT_FOUND


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
    admin: AdminUserDep,
) -> list[PermissionSchema]:
    if "permissions.view" not in current_user_permissions:
        raise GetPermissionsResponses.PERMISSION_ERROR

    try:
        permissions = await permissions_service.get_user_permissions(user_id)
    except ValueError:
        raise GetPermissionsResponses.USER_NOT_FOUND

    return [PermissionSchema.from_orm(permission) for permission in permissions]


class ManagePermissionsResponses(PermissionsResponses):
    PERMISSION_ERROR = 403, "Don't have enough permissions to manage user permissions"
    USER_NOT_FOUND = 404, "User with provided ID not found"


@router.put("/{user_id}/permissions", responses=ManagePermissionsResponses.responses, summary="Set user permissions")
async def set_user_permissions(
    user_id: Annotated[int, Path()],
    permissions_service: PermissionServiceDep,
    user_service: UserServiceDep,
    current_user_permissions: AdminPermissionsDep,
    admin: AdminUserDep,
    permissions_ids: list[int],
):
    if "permissions.update" not in current_user_permissions:
        raise ManagePermissionsResponses.PERMISSION_ERROR

    user = await user_service.get_user_by_kwargs(id=user_id)
    if not user:
        raise ManagePermissionsResponses.USER_NOT_FOUND

    try:
        request_time_utc = datetime.now(timezone.utc).isoformat()
        return await permissions_service.set_users_permissions(
            user_id, permissions_ids, admin, request_time_utc=request_time_utc
        )
    except ValueError:
        raise ManagePermissionsResponses.USER_NOT_FOUND
