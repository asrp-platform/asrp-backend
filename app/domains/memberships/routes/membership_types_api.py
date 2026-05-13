from fastapi import APIRouter

from app.domains.memberships.schemas import MembershipTypeSchema
from app.domains.memberships.services import MembershipServiceDep

router = APIRouter(prefix="/membership-types", tags=["Membership Types"])


@router.get("", summary="Get all membership types")
async def get_membership_types(
    membership_service: MembershipServiceDep,
) -> list[MembershipTypeSchema]:
    return await membership_service.get_membership_types()
