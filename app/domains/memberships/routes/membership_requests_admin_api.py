from typing import Annotated

from fastapi import APIRouter, Depends

from app.core.common.request_params import OrderingParamsDep, PaginationParamsDep
from app.core.common.responses import PaginatedResponse
from app.domains.memberships.filters import MembershipRequestsFilters
from app.domains.memberships.schemas import MembershipRequestViewSchema
from app.domains.memberships.use_cases.get_membership_requests_admin import GetMembershipRequestsAdminUseCaseDep
from app.domains.shared.deps import AdminPermissionsDep

router = APIRouter(prefix="/membership-requests", tags=["Admin: Membership"])


@router.get("/")
async def get_membership_requests(
    permissions: AdminPermissionsDep,
    use_case: GetMembershipRequestsAdminUseCaseDep,
    params: PaginationParamsDep,
    ordering: OrderingParamsDep = None,
    filters: Annotated[MembershipRequestsFilters, Depends()] = None,
) -> PaginatedResponse[MembershipRequestViewSchema]:
    data, count = await use_case.execute(
        permissions,
        order_by=ordering,
        filters=filters.model_dump(exclude_none=True),
        limit=params["limit"],
        offset=params["offset"],
    )
    return PaginatedResponse(
        count=count,
        data=data,
        page=params["page"],
        page_size=params["page_size"],
    )
