from fastapi import APIRouter, HTTPException, status
from fastapi_exception_responses import Responses

from app.domains.memberships.exceptions import MembershipTypeNotFoundError
from app.domains.feedback.exceptions import FeedbackAdditionalInfoAlreadyExistsError
from app.domains.memberships.exceptions import MembershipAlreadyExistsError
from app.domains.memberships.schemas import UserMembershipMockUpdateSchema, UserMembershipViewSchema
from app.domains.memberships.schemas import MembershipDataSchema
from app.domains.memberships.use_cases.create_membership import CreateMembershipUseCaseDep
from app.domains.memberships.use_cases.update_user_membership_mock import (
    UpdateUserMembershipMockRequest,
    UpdateUserMembershipMockUseCaseDep,
)
from app.domains.shared.deps import CurrentUserDep, CurrentUserMembershipDep

router = APIRouter(tags=["Current User"], prefix="/current-user")


@router.get("/membership", response_model=UserMembershipViewSchema)
async def get_current_user_membership(
    membership: CurrentUserMembershipDep,
):
    if membership is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Membership not found for the current user",
        )
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
    try:
        request = UpdateUserMembershipMockRequest(
            user_id=user.id,
            approval_status=update_data.approval_status,
            current_period_end=update_data.current_period_end,
            auto_renewal=update_data.auto_renewal,
            membership_type=update_data.membership_type,
            updated_fields=set(update_data.model_fields_set),
        )
        return await update_use_case.execute(request)
    except MembershipTypeNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
