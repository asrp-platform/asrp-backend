
from fastapi import APIRouter
from fastapi_exception_responses import Responses

from app.domains.feedback.services import AdditionalDetailServiceDep
from app.domains.memberships.exceptions import MembershipAlreadyExistsError
from app.domains.memberships.schemas import MembershipDataSchema
from app.domains.memberships.services import MembershipServiceDep
from app.domains.shared.deps import CurrentUserDep

router = APIRouter(tags=["Memberships"], prefix="/memberships")


class MembershipResponses(Responses):
    MEMBERSHIP_ALREADY_EXISTS = 409, "Membership for provided User already exists"


@router.post(
    "",
    status_code=201,
    responses=MembershipResponses.responses,
    summary="Create membership for a user"
)
async def create_membership(
    membership_data: MembershipDataSchema,
    current_user: CurrentUserDep,
    additional_detail_service: AdditionalDetailServiceDep,
    # после мержа https://github.com/asrp-platform/asrp-backend/pull/16 раскомментировать
    # communication_preference_service: CommunicationPreferenceServiceDep
    membership_service: MembershipServiceDep
) -> None:
    try:
        await membership_service.create_membership(
            current_user.id,
            membership_data.membership_type,
            **membership_data.membership.model_dump()
        )

        await additional_detail_service.create_additional_detail(
            current_user.id,
            **membership_data.additional_detail.model_dump()
        )

        # после мержа https://github.com/asrp-platform/asrp-backend/pull/16 раскомментировать
        # await communication_preference_service.create_communication_preference(membership_data.is_agrees_communications)

    except MembershipAlreadyExistsError:
        raise MembershipResponses.MEMBERSHIP_ALREADY_EXISTS

