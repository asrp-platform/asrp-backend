from typing import Annotated

from fastapi import APIRouter, Depends, File, UploadFile
from fastapi_exception_responses import Responses

from app.core.common.request_params import OrderingParamsDep, PaginationParamsDep
from app.core.common.responses import PaginatedResponse
from app.domains.memberships.schemas import (
    MembershipRequestCreateSchema,
    MembershipRequestViewSchema,
)
from app.domains.memberships.use_cases.create_membership_request import CreateMembershipRequestUseCaseDep
from app.domains.payments.filters import PaymentsFilter
from app.domains.payments.schemas import PaymentReadSchema
from app.domains.shared.deps import CurrentUserDep
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
from app.domains.users.services import UserServiceDep
from app.domains.users.use_cases.current_user.change_current_user_password import ChangeCurrentUserPasswordUseCaseDep
from app.domains.users.use_cases.current_user.delete_current_user_avatar import DeleteCurrentUserAvatarUseCaseDep
from app.domains.users.use_cases.current_user.get_current_user_membership import (
    GetCurrentUserMembershipRequestUseCaseDep,
)
from app.domains.users.use_cases.current_user.request_name_change import RequestNageChangeUseCaseDep
from app.domains.users.use_cases.current_user.retrieve_current_user_payments import (
    RetrieveCurrentUserPaymentsUseCaseDep,
)
from app.domains.users.use_cases.current_user.set_current_user_avatar import UploadCurrentUserAvatarUseCaseDep
from app.domains.users.use_cases.current_user.update_current_user import UpdateCurrentUserUseCaseDep

router = APIRouter(tags=["Current user"], prefix="/users/current-user")


@router.get("")
async def get_current_user(current_user: CurrentUserDep) -> UserSchema:
    return current_user


class UpdateUserDataResponses(Responses):
    USER_NOT_FOUND = 404, "User with the provided email was not found"


@router.patch("", summary="Update current authenticated user", responses=UpdateUserDataResponses.responses)
async def update_user(
    current_user: CurrentUserDep, update_data: UpdateUserSchema, use_case: UpdateCurrentUserUseCaseDep
) -> UserSchema:
    return await use_case.execute(current_user, **update_data.model_dump(exclude_unset=True))


@router.get(
    "/avatar",
)
async def get_user_avatar(
    current_user: CurrentUserDep,
    user_service: UserServiceDep,
) -> str | None:
    # Using use case here is overhead
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
    return await use_case.execute(current_user, file)


class DeleteUserAvatarResponses(UpdateUserDataResponses):
    pass


@router.delete(
    "/avatar",
    summary="Delete user avatar",
    responses=DeleteUserAvatarResponses.responses,
    status_code=204,
)
async def remove_user_avatar(
    use_case: DeleteCurrentUserAvatarUseCaseDep,
    current_user: CurrentUserDep,
):
    await use_case.execute(current_user)


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
    try:
        await use_case.execute(current_user, new_password=data.new_password, old_password=data.old_password)
    except InvalidPasswordError:
        raise ChangePasswordResponses.INVALID_PASSWORD


class NameChangeRequestResponses(Responses):
    PENDING_NAME_CHANGE_REQUEST_ALREADY_EXISTS = 409, "Pending name change request already exists"
    NAME_CHANGE_REQUEST_COOLDOWN_NOT_EXPIRED = 429, "Name change request cooldown not expired"


@router.post(
    "/name-change-requests",
    status_code=201,
    responses=NameChangeRequestResponses.responses,
    summary="Create request to change user firstname and lastname",
)
async def create_name_change_request(
    use_case: RequestNageChangeUseCaseDep,
    current_user: CurrentUserDep,
    name_change_request_data: NameChangeRequestCreateSchema,
) -> NameChangeRequestViewSchema:
    try:
        return await use_case.execute(current_user, **name_change_request_data.model_dump(exclude_none=True))

    except PendingNameChangeRequestAlreadyExistsError:
        raise NameChangeRequestResponses.PENDING_NAME_CHANGE_REQUEST_ALREADY_EXISTS

    except NameChangeRequestCooldownNotExpiredError:
        raise NameChangeRequestResponses.NAME_CHANGE_REQUEST_COOLDOWN_NOT_EXPIRED


class CurrentUserMembershipResponses(Responses):
    MEMBERSHIP_NOT_FOUND = 404, "Membership not found for the current user"


@router.get(
    "/membership-requests",
    response_model=MembershipRequestViewSchema,
    responses=CurrentUserMembershipResponses.responses,
)
async def get_current_user_membership(
    current_user: CurrentUserDep, use_case: GetCurrentUserMembershipRequestUseCaseDep
) -> MembershipRequestViewSchema:
    return await use_case.execute(current_user)


class MembershipCreateResponses(Responses):
    MEMBERSHIP_ALREADY_EXISTS = 409, "Membership for provided User already exists"
    FEEDBACK_ADDITIONAL_INFO_ALREADY_EXISTS = 409, "Additional Detail for provided User already exists"


@router.post(
    "/membership-requests",
    status_code=201,
    responses=MembershipCreateResponses.responses,
    summary="Create a membership request for current user",
)
async def create_membership_request(
    create_membership_request_data: MembershipRequestCreateSchema,
    current_user: CurrentUserDep,
    use_case: CreateMembershipRequestUseCaseDep,
) -> str:
    return await use_case.execute(
        user_id=current_user.id,
        is_agrees_communications=create_membership_request_data.is_agrees_communications,
        membership_type=create_membership_request_data.membership_type,
        membership_request_data=create_membership_request_data.membership.model_dump(),
        feedback_additional_info_data=create_membership_request_data.feedback_additional_info.model_dump(),
    )


@router.get("/payments")
async def get_current_user_payments(
    current_user: CurrentUserDep,
    use_case: RetrieveCurrentUserPaymentsUseCaseDep,
    params: PaginationParamsDep,
    ordering: OrderingParamsDep = None,
    filters: Annotated[PaymentsFilter, Depends()] = None,
) -> PaginatedResponse[PaymentReadSchema]:
    payments, count = await use_case.execute(
        current_user,
        order_by=ordering,
        filters=filters.model_dump(exclude_none=True),
        limit=params["limit"],
        offset=params["offset"],
    )
    return PaginatedResponse(
        count=count,
        data=payments,
        page=params["page"],
        page_size=params["page_size"],
    )
