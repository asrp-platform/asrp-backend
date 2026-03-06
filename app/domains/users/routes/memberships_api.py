from fastapi import APIRouter, HTTPException, status
from app.domains.shared.deps import CurrentUserDep, CurrentUserMembershipDep
from app.domains.memberships.services import MembershipsServiceDep
from app.domains.memberships.schemas import UserMembershipOut, UpdateUserMembershipMockIn

router = APIRouter(tags=["Users"], prefix="/users")


@router.get("/current-user/membership", response_model=UserMembershipOut)
async def get_current_user_membership(
    membership: CurrentUserMembershipDep,
):
    if membership is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Membership not found for the current user",
        )
    return membership


@router.patch("/current-user/membership/mock", response_model=UserMembershipOut)
async def update_current_user_membership_mock(
    user: CurrentUserDep,
    update_data: UpdateUserMembershipMockIn,
    memberships_service: MembershipsServiceDep,
):
    """
    TEMP: Mock endpoint for development/testing membership status and periods.
    Will be removed after payment integration.
    """
    from app.domains.memberships.exceptions import MembershipTypeNotFoundError
    try:
        return await memberships_service.update_user_membership_mock(
            user_id=user.id,
            approval_status=update_data.approval_status,
            current_period_end=update_data.current_period_end,
            cancel_at_period_end=update_data.cancel_at_period_end,
            auto_renewal=update_data.auto_renewal,
            membership_type_id=update_data.membership_type_id,
        )
    except MembershipTypeNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
