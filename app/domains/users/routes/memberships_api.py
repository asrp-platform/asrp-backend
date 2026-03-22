from fastapi import APIRouter, HTTPException, status

from app.domains.memberships.exceptions import MembershipTypeNotFoundError
from app.domains.memberships.schemas import UserMembershipMockUpdateSchema, UserMembershipViewSchema
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
