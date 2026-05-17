from typing import Annotated

from fastapi import APIRouter, Depends

from app.domains.memberships.filters import MembershipTypesFilters
from app.domains.memberships.schemas import MembershipTypeSchema
from app.domains.memberships.services import MembershipServiceDep

router = APIRouter(prefix="/membership-types", tags=["Membership Types"])


@router.get("", summary="Get all membership types")
async def get_membership_types(
    membership_service: MembershipServiceDep,
    filters: Annotated[MembershipTypesFilters, Depends()] = None,
) -> list[MembershipTypeSchema]:
    return await membership_service.get_membership_types(filters=filters.model_dump(exclude_none=True))
