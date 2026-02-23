import os
from typing import Annotated

from fastapi import APIRouter, Depends, File, Path, UploadFile
from fastapi_exception_responses import Responses

from app.core.common.exceptions import NotResourceOwnerError
from app.core.common.request_params import OrderingParamsDep, PaginationParamsDep
from app.core.common.responses import InvalidRequestParamsResponses, PaginatedResponse
from app.core.config import BASE_DIR, settings
from app.core.database.base_repository import InvalidOrderAttributeError
from app.core.utils.save_file import save_file
from app.domains.shared.deps import CurrentUserDep
from app.domains.users.exceptions import (
    PendingNameChangeRequestAlreadyExistsError,
    InvalidPasswordError,
    NameChangeRequestCooldownNotExpiredError,
    UserNotFoundError,
)
from app.domains.users.filters import UsersFilter
from app.domains.users.schemas import (
    ChangePasswordSchema,
    UpdateUserSchema,
    NameChangeRequestCreateSchema,
    NameChangeRequestViewSchema,
    UserSchema,
)
from app.domains.users.services import NameChangeRequestServiceDep, UserServiceDep

router = APIRouter(tags=["Users"], prefix="/users")


class UserListResponses(InvalidRequestParamsResponses):
    pass


@router.get("")
async def get_users(
    user_service: UserServiceDep,
    params: PaginationParamsDep,
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


@router.get("/current-user")
async def get_current_user(current_user: CurrentUserDep) -> UserSchema:
    return current_user


class GetUserResponses(Responses):
    USER_NOT_FOUND = 404, "User with the provided email was not found"


@router.get("/{user_id}", summary="Get user by id", responses=GetUserResponses.responses)
async def get_user(
    user_id: Annotated[int, Path(...)],
    user_service: UserServiceDep,
) -> UserSchema:
    user = await user_service.get_user_by_kwargs(id=user_id)
    if user is None:
        raise GetUserResponses.USER_NOT_FOUND
    return UserSchema.from_orm(user)


class UpdateUserDataResponses(Responses):
    USER_NOT_FOUND = 404, "User with the provided email was not found"
    PERMISSION_DENIED = 403, "You do not have permission to update this user"


@router.put("/{user_id}", summary="Update user data", responses=UpdateUserDataResponses.responses)
async def update_user_data(
    user_service: UserServiceDep,
    current_user: CurrentUserDep,
    user_id: Annotated[int, Path(...)],
    update_data: UpdateUserSchema | None = None,
) -> UserSchema:
    if not (current_user.id == user_id or current_user.stuff):
        raise UpdateUserDataResponses.PERMISSION_DENIED

    try:
        user = await user_service.update_user(user_id=user_id, update_data=update_data.model_dump(exclude_none=True))
    except UserNotFoundError:
        raise UpdateUserDataResponses.USER_NOT_FOUND
    return UserSchema.from_orm(user)


class SetAvatarResponses(Responses):
    INVALID_CONTENT_TYPE = 422, "Invalid avatar content type"
    USER_NOT_FOUND = 404, "User with provided id not found"


@router.put(
    "/{user_id}/avatar",
    responses=SetAvatarResponses.responses,
    summary="Upload user avatar image",
)
async def upload_user_avatar(
    user_service: UserServiceDep,
    current_user: CurrentUserDep,  # noqa
    user_id: Annotated[int, Path()],
    file: Annotated[UploadFile, File(...)],
):
    if not file.content_type.startswith("image/"):
        raise SetAvatarResponses.INVALID_CONTENT_TYPE

    relative_filepath = await save_file(file, settings.MEDIA_STORAGE_PATH)

    try:
        await user_service.set_user_avatar(user_id=user_id, avatar_path=str(relative_filepath))
    except UserNotFoundError:
        os.remove(BASE_DIR / relative_filepath)
        raise SetAvatarResponses.USER_NOT_FOUND

    return {"path": relative_filepath.as_posix()}


class DeleteUserAvatarResponses(Responses):
    USER_NOT_FOUND = 404, "User with provided id not found"


@router.delete(
    "/{user_id}/avatar",
    summary="Delete user avatar",
    responses=DeleteUserAvatarResponses.responses,
)
async def remove_user_avatar(
    user_id: Annotated[int, Path()],
    user_service: UserServiceDep,
    current_user: CurrentUserDep,  # noqa
):
    try:
        await user_service.delete_avatar(user_id)
    except ValueError:
        raise DeleteUserAvatarResponses.USER_NOT_FOUND


class ChangePasswordResponses(Responses):
    INVALID_PASSWORD = 403, "Invalid password"
    USER_NOT_FOUND = 404, "User with provided ID not found"


@router.post(
    "/{user_id}/password-change",
    responses=ChangePasswordResponses.responses,
    summary="Changes user password",
)
async def change_user_password(
    user_id: Annotated[int, Path()],
    user_service: UserServiceDep,
    current_user: CurrentUserDep,  # noqa
    data: ChangePasswordSchema,
) -> None:
    try:
        await user_service.change_password(user_id, data.old_password, data.new_password)
    except ValueError:
        raise ChangePasswordResponses.USER_NOT_FOUND
    except InvalidPasswordError:
        raise ChangePasswordResponses.INVALID_PASSWORD


class NameChangeRequestResponses(Responses):
    NOT_RESOURCE_OWNER = 403, "Not resource owner"
    PENDING_NAME_CHANGE_REQUEST_ALREADY_EXISTS = 409, "Pending name change request already exists"
    NAME_CHANGE_REQUEST_COOLDOWN_NOT_EXPIRED = 429, "Name change request cooldown not expired"


@router.post(
    "/{user_id}/name-change-requests",
    status_code=201,
    responses=NameChangeRequestResponses.responses,
    summary="Create request to change user firstname and lastname"
)
async def create_name_change_request(
    user_id: Annotated[int, Path()],
    service: NameChangeRequestServiceDep,
    current_user: CurrentUserDep,
    name_change_request_data: NameChangeRequestCreateSchema
) -> NameChangeRequestViewSchema:
    try:
        name_change_request = await service.create_name_change_request(
            user_id,
            **name_change_request_data.model_dump()
        )
        return NameChangeRequestViewSchema.model_validate(name_change_request)

    except NotResourceOwnerError:
        raise NameChangeRequestResponses.NOT_RESOURCE_OWNER

    except PendingNameChangeRequestAlreadyExistsError:
        raise NameChangeRequestResponses.PENDING_NAME_CHANGE_REQUEST_ALREADY_EXISTS

    except NameChangeRequestCooldownNotExpiredError:
        raise NameChangeRequestResponses.NAME_CHANGE_REQUEST_COOLDOWN_NOT_EXPIRED
