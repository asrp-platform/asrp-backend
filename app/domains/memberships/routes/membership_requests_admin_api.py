from fastapi import APIRouter

from app.domains.memberships.services import MembershipServiceDep

router = APIRouter(prefix="/membership-requests", tags=["Admin: Membership"])


@router.get("/")
async def get_membership_requests(
    # admin: AdminUserDep,
    service: MembershipServiceDep,
):
    return await service.get_membership_requests()
