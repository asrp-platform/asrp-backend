from typing import Annotated

from fastapi import APIRouter, Depends

from app.core.common.request_params import OrderingParamsDep, PaginationParamsDep
from app.core.common.responses import PaginatedResponse
from app.domains.memberships.filters import UserMembershipTypeChangeRequestsFilters
from app.domains.memberships.schemas.type_change_schemas import (
    ReviewMembershipTypeChangeRequest,
    UserMembershipTypeChangeRequestViewSchema,
)
from app.domains.memberships.use_cases.memberships.get_type_change_requests import GetTypeChangeRequestsUseCaseDep
from app.domains.shared.deps import AdminPermissionsDep, get_admin_user

router = APIRouter(prefix="/memberships", tags=["Admin: Memberships"], dependencies=[Depends(get_admin_user)])


@router.get("/types/change-requests", summary="Get all membership type change requests")
async def get_membership_type_change_requests(
    permissions: AdminPermissionsDep,
    use_case: GetTypeChangeRequestsUseCaseDep,
    params: PaginationParamsDep,
    ordering: OrderingParamsDep = None,
    filters: Annotated[UserMembershipTypeChangeRequestsFilters, Depends()] = None,
) -> PaginatedResponse[UserMembershipTypeChangeRequestViewSchema]:
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


@router.patch("/types/change-requests/{request_id}", summary="Get membership type change request by ID")
async def get_membership_type_changer_request(
    request_id: int,
    body: ReviewMembershipTypeChangeRequest,
):
    pass
