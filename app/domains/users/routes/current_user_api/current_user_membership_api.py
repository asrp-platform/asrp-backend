from fastapi import APIRouter, Response
from fastapi_exception_responses import Responses

from app.domains.feedback.exceptions import FeedbackAdditionalInfoAlreadyExistsError
from app.domains.memberships.exceptions import (
    CantBuyHonoraryMembership,
    CantChangeToHonoraryMembershipError,
    CheckoutSessionCreationError,
    InvalidMembershipTypeDowngradeError,
    InvalidMembershipTypeUpgradeError,
    MembershipAlreadyPaidError,
    MembershipRequestCannotBeReappliedError,
    MembershipSuspendedError,
    MembershipTerminatedError,
    NoMembershipError,
    SameMembershipTypeChangeRequestError,
)
from app.domains.memberships.schemas.membership_requests import (
    MembershipDowngradeCreateCreateSchema,
    MembershipRequestCreateSchema,
    MembershipRequestReapplySchema,
    MembershipRequestViewSchema,
    UpgradeMembershipSchema,
)
from app.domains.memberships.schemas.membership_types import UserMembershipTypeChangeRequestProfileSchema
from app.domains.memberships.schemas.user_memberships import MembershipConfirmationSchema, UserMembershipSchema
from app.domains.memberships.services import UserMembershipServiceDep
from app.domains.payments.schemas import PaymentCheckoutSchema
from app.domains.shared.deps import CurrentUserDep, CurrentUserMembershipDep
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
from app.domains.users.use_cases.current_user_membership.get_membership_confirmation import (
    GetMembershipConfirmationUseCaseDep,
)
from app.domains.users.use_cases.current_user_membership.get_membership_confirmation_pdf import (
    GetMembershipConfirmationPdfUseCaseDep,
)
from app.domains.users.use_cases.current_user_membership.reapply_membership_application import (
    ReapplyMembershipApplicationUseCaseDep,
)
from app.domains.users.use_cases.current_user_membership.renew_membership import RenewMembershipUseCaseDep
from app.domains.users.use_cases.current_user_membership.request_membership_downgrade import (
    RequestMembershipDowngradeUseCaseDep,
)
from app.domains.users.use_cases.current_user_membership.upgrade_membership import UpgradeMembershipUseCaseDep


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
            current_user=current_user,
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
    except CheckoutSessionCreationError:
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
    except CheckoutSessionCreationError:
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
    except CheckoutSessionCreationError:
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


class UpgradeMembershipResponses(Responses):
    INVALID_TOKEN = 401, "Invalid token"
    NO_ACTIVE_MEMBERSHIP = 403, "No active membership"
    MEMBERSHIP_PERMANENTLY_BLOCKED = 403, "Membership is permanently blocked"
    MEMBERSHIP_TEMPORARILY_BLOCKED = 403, "Membership is temporarily blocked"
    MEMBERSHIP_TYPE_NOT_FOUND = 404, "Provided membership type not found"
    SAME_MEMBERSHIP_TYPE = 422, "Can't change membership type for the same type"
    CANT_CHANGE_TO_HONORARY_MEMBERSHIP = 422, "Can't change membership type to HONORARY"
    INVALID_UPGRADE = 422, "Invalid membership type upgrade"
    CHECKOUT_SESSION_CREATION_FAILED = 502, "Failed to create checkout session"


@router.post(
    "/membership/upgrade",
    summary="Create a checkout for membership type upgrade",
    status_code=201,
    responses=UpgradeMembershipResponses.responses,
)
async def create_membership_upgrade_checkout(
    current_user: CurrentUserDep,
    current_user_membership: CurrentUserMembershipDep,
    use_case: UpgradeMembershipUseCaseDep,
    body: UpgradeMembershipSchema,
) -> PaymentCheckoutSchema:
    try:
        checkout_session_url = await use_case.execute(
            current_user_membership,
            current_user,
            body.target_membership_type_id,
        )
    except SameMembershipTypeChangeRequestError:
        raise UpgradeMembershipResponses.SAME_MEMBERSHIP_TYPE
    except CantChangeToHonoraryMembershipError:
        raise UpgradeMembershipResponses.CANT_CHANGE_TO_HONORARY_MEMBERSHIP
    except InvalidMembershipTypeUpgradeError:
        raise UpgradeMembershipResponses.INVALID_UPGRADE
    except CheckoutSessionCreationError:
        raise UpgradeMembershipResponses.CHECKOUT_SESSION_CREATION_FAILED

    return PaymentCheckoutSchema(checkout_session_url=checkout_session_url)


class RenewMembershipResponses(Responses):
    INVALID_TOKEN = 401, "Invalid token"
    NO_MEMBERSHIP = 403, "No active membership"
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
    current_user: CurrentUserDep,
    use_case: RenewMembershipUseCaseDep,
) -> PaymentCheckoutSchema:
    try:
        checkout_session_url = await use_case.execute(current_user)
    except NoMembershipError:
        raise RenewMembershipResponses.NO_MEMBERSHIP
    except CheckoutSessionCreationError:
        raise RenewMembershipResponses.CHECKOUT_SESSION_CREATION_FAILED
    except MembershipTerminatedError:
        raise RenewMembershipResponses.MEMBERSHIP_PERMANENTLY_BLOCKED
    except MembershipSuspendedError:
        raise RenewMembershipResponses.MEMBERSHIP_TEMPORARILY_BLOCKED

    return PaymentCheckoutSchema(checkout_session_url=checkout_session_url)


class MembershipConfirmationResponses(Responses):
    MEMBERSHIP_NOT_FOUND = 404, "Membership for the current user not found"


MEMBERSHIP_CONFIRMATION_PDF_RESPONSES = {
    **MembershipConfirmationResponses.responses,
    200: {
        "description": "Membership confirmation PDF generated for the current user",
        "content": {
            "application/pdf": {
                "schema": {
                    "type": "string",
                    "format": "binary",
                }
            }
        },
        "headers": {
            "Content-Disposition": {
                "description": "Attachment filename generated from the membership ID",
                "schema": {
                    "type": "string",
                    "example": (
                        'attachment; filename="membership-confirmation-ASRP-2024-00123.pdf"'
                    ),
                },
            }
        },
    },
}


@router.get(
    "/membership/confirmation",
    summary="Get membership confirmation for current user",
    responses=MembershipConfirmationResponses.responses,
)
async def get_membership_confirmation(
    current_user: CurrentUserDep,
    use_case: GetMembershipConfirmationUseCaseDep,
) -> MembershipConfirmationSchema:
    return await use_case.execute(current_user)


@router.get(
    "/membership/confirmation/pdf",
    summary="Download membership confirmation PDF for current user",
    description="""
Generates the PDF on demand and returns it directly in the response body.

The response is binary data, not JSON. With the frontend Axios client, request it as a `Blob`:

```ts
const response = await api.get(
    "/users/current-user/membership/confirmation/pdf",
    { responseType: "blob" },
)

const disposition = response.headers["content-disposition"]
const filename = disposition?.match(/filename="([^"]+)"/)?.[1]
    ?? "membership-confirmation.pdf"
const fileUrl = URL.createObjectURL(response.data)
const link = document.createElement("a")
link.href = fileUrl
link.download = filename
link.click()
URL.revokeObjectURL(fileUrl)
```

The generated filename is also returned in the exposed `Content-Disposition` response header.
""",
    response_class=Response,
    responses=MEMBERSHIP_CONFIRMATION_PDF_RESPONSES,
)
async def get_membership_confirmation_pdf(
    current_user: CurrentUserDep,
    use_case: GetMembershipConfirmationPdfUseCaseDep,
) -> Response:
    pdf = await use_case.execute(current_user)
    return Response(
        content=pdf.content,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{pdf.filename}"'},
    )
