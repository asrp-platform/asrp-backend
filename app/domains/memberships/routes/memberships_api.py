from fastapi import APIRouter
from fastapi_exception_responses import Responses

from app.domains.memberships.exceptions import MembershipAlreadyExistsError
from app.domains.memberships.schemas import MembershipDataSchema
from app.domains.shared.deps import CurrentUserDep
from app.use_cases.create_membership import CreateMembershipUseCaseDep

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
    create_membership_use_case: CreateMembershipUseCaseDep
) -> None:
    try:
        await create_membership_use_case.execute(
            user_id=current_user.id,
            is_agrees_communications=membership_data.is_agrees_communications,
            membership_type=membership_data.membership_type,
            user_membership_data=membership_data.membership.model_dump(),
            additional_detail_data=membership_data.additional_detail.model_dump()
        )

    except MembershipAlreadyExistsError:
        raise MembershipResponses.MEMBERSHIP_ALREADY_EXISTS

