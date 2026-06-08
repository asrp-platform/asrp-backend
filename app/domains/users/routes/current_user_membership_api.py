from fastapi import APIRouter
from fastapi_exception_responses import Responses

from app.domains.feedback.exceptions import FeedbackAdditionalInfoAlreadyExistsError
from app.domains.memberships.exceptions import (
    CantBuyHonoraryMembership,
    CantChangeToHonoraryMembershipError,
    InvalidMembershipTypeDowngradeError,
    InvalidMembershipTypeUpgradeError,
    MembershipAlreadyPaidError,
    MembershipApplicationCheckoutError,
    MembershipRenewalCheckoutError,
    MembershipRequestCannotBeReappliedError,
    SameMembershipTypeChangeRequestError,
)
from app.domains.memberships.schemas.membership_downgrade_schemas import UserMembershipTypeChangeRequestProfileSchema
from app.domains.memberships.schemas.membership_schemas import UserMembershipSchema
from app.domains.memberships.schemas.schemas import (
    MembershipDowngradeCreateCreateSchema,
    MembershipRequestCreateSchema,
    MembershipRequestReapplySchema,
    MembershipRequestViewSchema,
)
from app.domains.memberships.services import UserMembershipServiceDep
from app.domains.shared.deps import CurrentUserDep, CurrentUserMembershipDep
from app.domains.shared.schemas import PaymentCheckoutSchema
from app.domains.users.use_cases.current_user_membership.create_membership_application_payment_attempt import (
    CreateMembershipApplicationPaymentAttemptUseCaseDep,
)
from app.domains.users.use_cases.current_user_membership.create_membership_request import (
    CreateMembershipRequestUseCaseDep,
)
from app.domains.users.use_cases.current_user_membership.get_current_user_membership import (
    GetCurrentUserMembershipRequestUseCaseDep,
)
from app.domains.users.use_cases.current_user_membership.get_current_user_membership_downgrade_request import (
    GetCurrentUserMembershipDowngradeRequestUseCaseDep,
)
from app.domains.users.use_cases.current_user_membership.reapply_membership_application import (
    ReapplyMembershipApplicationUseCaseDep,
)
from app.domains.users.use_cases.current_user_membership.renew_membership import RenewMembershipUseCaseDep
from app.domains.users.use_cases.current_user_membership.request_membership_downgrade import (
    RequestMembershipDowngradeUseCaseDep,
)

router = APIRouter(tags=["Current User: Membership"], prefix="/users/current-user")


@router.get(
    "/membership-requests",
)
async def get_current_user_membership_request(
    current_user: CurrentUserDep, use_case: GetCurrentUserMembershipRequestUseCaseDep
) -> MembershipRequestViewSchema | None:
    return await use_case.execute(current_user)


class MembershipCreateResponses(Responses):
    MEMBERSHIP_ALREADY_EXISTS = 409, "Membership for provided User already exists"
    FEEDBACK_ADDITIONAL_INFO_ALREADY_EXISTS = 409, "Additional Detail for provided User already exists"
    CANT_BUY_HONORARY_MEMBERSHIP = 422, "Can't purchase HONORARY membership"
    CHECKOUT_SESSION_CREATION_FAILED = 502, "Failed to create checkout session"


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
) -> PaymentCheckoutSchema:
    try:
        checkout_session_url = await use_case.execute(
            user_id=current_user.id,
            is_agrees_communications=create_membership_request_data.is_agrees_communications,
            membership_type=create_membership_request_data.membership_type,
            membership_request_data=create_membership_request_data.membership.model_dump(),
            feedback_additional_info_data=create_membership_request_data.feedback_additional_info.model_dump(),
        )
        return PaymentCheckoutSchema(checkout_session_url=checkout_session_url)
    except CantBuyHonoraryMembership:
        raise MembershipCreateResponses.CANT_BUY_HONORARY_MEMBERSHIP
    except FeedbackAdditionalInfoAlreadyExistsError:
        raise MembershipCreateResponses.FEEDBACK_ADDITIONAL_INFO_ALREADY_EXISTS
    except MembershipApplicationCheckoutError:
        raise MembershipCreateResponses.CHECKOUT_SESSION_CREATION_FAILED


class CreateNewPaymentAttemptResponses(Responses):
    MEMBERSHIP_REQUEST_NOT_FOUND = 404, "Membership request for the current user not found"
    MEMBERSHIP_REQUEST_ALREADY_PAID = 409, "Membership request for the current user already paid"
    CHECKOUT_SESSION_CREATION_FAILED = 502, "Failed to create checkout session"


@router.post(
    "/membership-requests/payments",
    status_code=201,
    responses=CreateNewPaymentAttemptResponses.responses,
    summary="Create a new payment attempt for the unpaid membership request",
)
async def create_new_payment_attempt(
    current_user: CurrentUserDep,
    use_case: CreateMembershipApplicationPaymentAttemptUseCaseDep,
) -> PaymentCheckoutSchema:
    try:
        checkout_session_url = await use_case.execute(current_user)
        return PaymentCheckoutSchema(checkout_session_url=checkout_session_url)
    except MembershipAlreadyPaidError:
        raise CreateNewPaymentAttemptResponses.MEMBERSHIP_REQUEST_ALREADY_PAID
    except MembershipApplicationCheckoutError:
        raise CreateNewPaymentAttemptResponses.CHECKOUT_SESSION_CREATION_FAILED


class ReapplyMembershipRequestResponses(Responses):
    MEMBERSHIP_REQUEST_NOT_FOUND = 404, "Membership request for the current user not found"
    MEMBERSHIP_REQUEST_CANNOT_BE_REAPPLIED = 409, "Cannot reapply not rejected membership request"
    MEMBERSHIP_REQUEST_ALREADY_PAID = 409, "Membership request for the current user already paid"
    CANT_BUY_HONORARY_MEMBERSHIP = 422, "Can't purchase HONORARY membership"
    CHECKOUT_SESSION_CREATION_FAILED = 502, "Failed to create checkout session"


@router.post(
    "/membership-requests/reapplies",
    status_code=201,
    responses=ReapplyMembershipRequestResponses.responses,
    summary="Reapply for a membership if membership request was rejected",
)
async def create_membership_request_reapply(
    current_user: CurrentUserDep,
    body: MembershipRequestReapplySchema,
    use_case: ReapplyMembershipApplicationUseCaseDep,
) -> PaymentCheckoutSchema:
    try:
        checkout_session_url = await use_case.execute(current_user, **body.model_dump())
        return PaymentCheckoutSchema(checkout_session_url=checkout_session_url)
    except MembershipAlreadyPaidError:
        raise ReapplyMembershipRequestResponses.MEMBERSHIP_REQUEST_ALREADY_PAID
    except MembershipRequestCannotBeReappliedError:
        raise ReapplyMembershipRequestResponses.MEMBERSHIP_REQUEST_CANNOT_BE_REAPPLIED
    except CantBuyHonoraryMembership:
        raise ReapplyMembershipRequestResponses.CANT_BUY_HONORARY_MEMBERSHIP
    except MembershipApplicationCheckoutError:
        raise ReapplyMembershipRequestResponses.CHECKOUT_SESSION_CREATION_FAILED


@router.get("/membership")
async def get_current_user_membership(
    current_user: CurrentUserDep,
    user_membership_service: UserMembershipServiceDep,
) -> UserMembershipSchema | None:
    return await user_membership_service.get_user_membership_by_user_id(current_user.id)


class MembershipTypeChangeRequestResponses(Responses):
    NO_ACTIVE_MEMBERSHIP = 403, "No active membership"
    PENDING_REQUEST_ALREADY_EXISTS = 409, "Pending user membership type change request already exists"
    SAME_MEMBERSHIP_TYPE = 422, "Can't change membership type for the same type"
    CANT_CHANGE_TO_HONORARY_MEMBERSHIP = 422, "Can't change membership type to HONORARY"
    INVALID_UPGRADE = 422, "Target membership type is not more expensive than current membership type"
    INVALID_DOWNGRADE = 422, "Target membership type is not cheaper than current membership type"


@router.post(
    "/membership/downgrade-request",
    summary="Create a request to downgrade membership type",
    responses=MembershipTypeChangeRequestResponses.responses,
    status_code=201,
)
async def request_membership_type_change(
    current_user_membership: CurrentUserMembershipDep,
    body: MembershipDowngradeCreateCreateSchema,
    use_case: RequestMembershipDowngradeUseCaseDep,
):
    try:
        return await use_case.execute(current_user_membership, **body.model_dump())
    except SameMembershipTypeChangeRequestError:
        raise MembershipTypeChangeRequestResponses.SAME_MEMBERSHIP_TYPE
    except CantChangeToHonoraryMembershipError:
        raise MembershipTypeChangeRequestResponses.CANT_CHANGE_TO_HONORARY_MEMBERSHIP
    except InvalidMembershipTypeUpgradeError:
        raise MembershipTypeChangeRequestResponses.INVALID_UPGRADE
    except InvalidMembershipTypeDowngradeError:
        raise MembershipTypeChangeRequestResponses.INVALID_DOWNGRADE


@router.get(
    "/membership/downgrade-request",
    summary="Get current user's membership downgrade request",
)
async def get_current_user_membership_type_change_request(
    current_user_membership: CurrentUserMembershipDep,
    use_case: GetCurrentUserMembershipDowngradeRequestUseCaseDep,
) -> UserMembershipTypeChangeRequestProfileSchema | None:
    return await use_case.execute(current_user_membership)


@router.delete("/membership/downgrade-request", summary="Cancel (delete) current user's membership downgrade request")
async def cancel_membership_downgrade_request(
    current_user_membership: CurrentUserMembershipDep,
):
    pass


@router.post(
    "/membership/upgrade-checkouts",
    summary="Create a checkout for membership type upgrade",
    status_code=201,
)
async def create_membership_upgrade_checkout(
    current_user_membership: CurrentUserMembershipDep,
):
    pass


class RenewMembershipResponses(Responses):
    NO_ACTIVE_MEMBERSHIP = 403, "No active membership"
    MEMBERSHIP_PERMANENTLY_BLOCKED = 403, "Membership is permanently blocked"
    MEMBERSHIP_TEMPORARILY_BLOCKED = 403, "Membership is temporarily blocked until 2026-06-08T12:00:00+00:00"
    CHECKOUT_SESSION_CREATION_FAILED = 502, "Failed to create checkout session"


@router.post(
    "/membership/renewal",
    status_code=201,
    responses=RenewMembershipResponses.responses,
    summary="Create membership renewal checkout session",
)
async def renew_membership(
    current_user_membership: CurrentUserMembershipDep,
    use_case: RenewMembershipUseCaseDep,
) -> PaymentCheckoutSchema:
    try:
        checkout_session_url = await use_case.execute(current_user_membership)
    except MembershipRenewalCheckoutError:
        raise RenewMembershipResponses.CHECKOUT_SESSION_CREATION_FAILED

    return PaymentCheckoutSchema(checkout_session_url=checkout_session_url)
