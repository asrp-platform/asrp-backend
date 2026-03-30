from typing import Annotated

from fastapi import APIRouter, File, UploadFile
from fastapi_exception_responses import Responses

from app.core.common.exceptions import NotResourceOwnerError
from app.domains.feedback.exceptions import FeedbackAdditionalInfoAlreadyExistsError
from app.domains.memberships.exceptions import MembershipAlreadyExistsError
from app.domains.memberships.schemas import (
    MembershipDataSchema,
    UserMembershipMockUpdateSchema,
    UserMembershipViewSchema,
)
from app.domains.memberships.use_cases.create_membership import CreateMembershipUseCaseDep
from app.domains.memberships.use_cases.update_user_membership_mock import (
    UpdateUserMembershipMockRequest,
    UpdateUserMembershipMockUseCaseDep,
)
from app.domains.shared.deps import CurrentUserDep, CurrentUserMembershipDep
from app.domains.users.exceptions import (
    InvalidPasswordError,
    NameChangeRequestCooldownNotExpiredError,
    PendingNameChangeRequestAlreadyExistsError,
)
from app.domains.users.schemas import (
    ChangePasswordSchema,
    NameChangeRequestCreateSchema,
    NameChangeRequestViewSchema,
    UpdateUserSchema,
    UserSchema,
)
from app.domains.users.services import NameChangeRequestServiceDep, UserServiceDep
from app.domains.users.use_cases.change_current_user_password import (
    ChangeCurrentUserPasswordRequest,
    ChangeCurrentUserPasswordUseCaseDep,
)
from app.domains.users.use_cases.delete_current_user_avatar import (
    DeleteCurrentUserAvatarRequest,
    DeleteCurrentUserAvatarUseCaseDep,
)
from app.domains.users.use_cases.set_current_user_avatar import (
    UploadCurrentUserAvatarRequest,
    UploadCurrentUserAvatarUseCaseDep,
)

router = APIRouter(tags=["Current user"], prefix="/users/current-user")


@router.get("")
async def get_current_user(current_user: CurrentUserDep) -> UserSchema:
    return current_user


class UpdateUserDataResponses(Responses):
    USER_NOT_FOUND = 404, "User with the provided email was not found"
    NOT_RESOURCE_OWNER = 403, "Not resource owner"


@router.patch("", summary="Update user data", responses=UpdateUserDataResponses.responses)
async def update_user_data(
    user_service: UserServiceDep,
    current_user: CurrentUserDep,
    update_data: UpdateUserSchema,
) -> UserSchema:
    user = await user_service.update_user(
        user_id=current_user.id, current_user=current_user, update_data=update_data.model_dump(exclude_none=True)
    )
    return UserSchema.from_orm(user)


@router.get(
    "/avatar",
)
async def get_user_avatar(
    current_user: CurrentUserDep,
    user_service: UserServiceDep,
) -> str | None:
    return await user_service.get_user_avatar_url(current_user.id)


class UploadAvatarResponses(UpdateUserDataResponses):
    INVALID_CONTENT_TYPE = 422, "Invalid avatar content type"


@router.put(
    "/avatar",
    responses=UploadAvatarResponses.responses,
    summary="Upload user avatar image",
)
async def upload_user_avatar(
    current_user: CurrentUserDep,
    use_case: UploadCurrentUserAvatarUseCaseDep,
    file: Annotated[UploadFile, File(...)],
) -> str:
    if not file.content_type.startswith("image/"):
        raise UploadAvatarResponses.INVALID_CONTENT_TYPE

    request = UploadCurrentUserAvatarRequest(current_user, file)
    return await use_case.execute(request)


class DeleteUserAvatarResponses(UpdateUserDataResponses):
    pass


@router.delete(
    "/avatar",
    summary="Delete user avatar",
    responses=DeleteUserAvatarResponses.responses,
    status_code=204,
)
async def remove_user_avatar(
    user_case: DeleteCurrentUserAvatarUseCaseDep,
    current_user: CurrentUserDep,
):
    request = DeleteCurrentUserAvatarRequest(current_user=current_user)
    await user_case.execute(request)


class ChangePasswordResponses(Responses):
    INVALID_PASSWORD = 403, "Invalid password"
    USER_NOT_FOUND = 404, "User with provided ID not found"


@router.post(
    "/password-change",
    responses=ChangePasswordResponses.responses,
    summary="Changes user password",
    status_code=204,
)
async def change_user_password(
    use_case: ChangeCurrentUserPasswordUseCaseDep,
    current_user: CurrentUserDep,  # noqa
    data: ChangePasswordSchema,
) -> None:
    request = ChangeCurrentUserPasswordRequest(
        current_user,
        new_password=data.new_password,
        old_password=data.old_password,
    )

    try:
        await use_case.execute(request)
    except InvalidPasswordError:
        raise ChangePasswordResponses.INVALID_PASSWORD


class NameChangeRequestResponses(Responses):
    NOT_RESOURCE_OWNER = 403, "Not resource owner"
    PENDING_NAME_CHANGE_REQUEST_ALREADY_EXISTS = 409, "Pending name change request already exists"
    NAME_CHANGE_REQUEST_COOLDOWN_NOT_EXPIRED = 429, "Name change request cooldown not expired"


@router.post(
    "/name-change-requests",
    status_code=201,
    responses=NameChangeRequestResponses.responses,
    summary="Create request to change user firstname and lastname",
)
async def create_name_change_request(
    service: NameChangeRequestServiceDep,
    current_user: CurrentUserDep,
    name_change_request_data: NameChangeRequestCreateSchema,
) -> NameChangeRequestViewSchema:
    try:
        name_change_request = await service.create_name_change_request(
            current_user.id, **name_change_request_data.model_dump(exclude_none=True)
        )
        return NameChangeRequestViewSchema.model_validate(name_change_request)

    except NotResourceOwnerError:
        raise NameChangeRequestResponses.NOT_RESOURCE_OWNER

    except PendingNameChangeRequestAlreadyExistsError:
        raise NameChangeRequestResponses.PENDING_NAME_CHANGE_REQUEST_ALREADY_EXISTS

    except NameChangeRequestCooldownNotExpiredError:
        raise NameChangeRequestResponses.NAME_CHANGE_REQUEST_COOLDOWN_NOT_EXPIRED


class CurrentUserMembershipResponses(Responses):
    MEMBERSHIP_NOT_FOUND = 404, "Membership not found for the current user"


@router.get(
    "/membership",
    response_model=UserMembershipViewSchema,
    responses=CurrentUserMembershipResponses.responses,
)
async def get_current_user_membership(
    membership: CurrentUserMembershipDep,
):
    if membership is None:
        raise CurrentUserMembershipResponses.MEMBERSHIP_NOT_FOUND
    return membership


class MembershipCreateResponses(Responses):
    MEMBERSHIP_ALREADY_EXISTS = 409, "Membership for provided User already exists"
    FEEDBACK_ADDITIONAL_INFO_ALREADY_EXISTS = 409, "Additional Detail for provided User already exists"


@router.post(
    "/membership",
    status_code=201,
    responses=MembershipCreateResponses.responses,
    summary="Create membership for a user"
)
async def create_membership(
    membership_data: MembershipDataSchema,
    current_user: CurrentUserDep,
    create_membership_use_case: CreateMembershipUseCaseDep
) -> None:
    try:
        await create_membership_use_case.execute(
            user_id=current_user.id,
            is_agrees_communications=membership_data.is_agrees_communications,
            membership_type=membership_data.membership_type,
            user_membership_data=membership_data.membership.model_dump(),
            feedback_additional_info_data=membership_data.feedback_additional_info.model_dump()
        )

    except MembershipAlreadyExistsError:
        raise MembershipCreateResponses.MEMBERSHIP_ALREADY_EXISTS
    except FeedbackAdditionalInfoAlreadyExistsError:
        raise MembershipCreateResponses.FEEDBACK_ADDITIONAL_INFO_ALREADY_EXISTS


@router.patch("/membership/mock", response_model=UserMembershipViewSchema)
async def update_current_user_membership_mock(
    user: CurrentUserDep,
    update_data: UserMembershipMockUpdateSchema,
    update_use_case: UpdateUserMembershipMockUseCaseDep,
):
    """
    TEMP: Mock endpoint for development/testing membership status and periods.
    """
    request = UpdateUserMembershipMockRequest(
        user_id=user.id,
        approval_status=update_data.approval_status,
        current_period_end=update_data.current_period_end,
        auto_renewal=update_data.auto_renewal,
        membership_type=update_data.membership_type,
        updated_fields=set(update_data.model_fields_set),
    )
    return await update_use_case.execute(request)
