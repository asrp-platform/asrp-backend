from fastapi import APIRouter

from app.domains.shared.deps import AdminUserDep

router = APIRouter(prefix="/membership-requests", tags=["Admin: Membership"])


@router.get("/")
async def get_membership_requests(
    admin: AdminUserDep,
    # service: Me
):
    pass
