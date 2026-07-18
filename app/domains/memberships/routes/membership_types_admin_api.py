from typing import Annotated

from fastapi import APIRouter, Depends

from app.core.common.request_params import OrderingParamsDep, PaginationParamsDep
from app.core.common.responses import PaginatedResponse
from app.core.utils.permissions import check_permissions
from app.domains.memberships.filters import MembershipTypesFilters, UserMembershipTypeChangeRequestsFilters
from app.domains.memberships.schemas.membership_types_schemas import (
    MembershipTypeSchema,
    ReviewedMembershipTypeChangeRequestSchema,
    ReviewMembershipTypeChangeRequest,
    UpdateMembershipTypeSchema,
    UserMembershipTypeChangeRequestViewSchema,
)
from app.domains.memberships.services import MembershipTypeServiceDep
from app.domains.memberships.use_cases.memberships.get_downgrade_requests import (
    GetMembershipDowngradeRequestsUseCaseDep,
)
from app.domains.memberships.use_cases.memberships.review_downgrade_request import (
    ReviewMembershipDowngradeRequestUseCaseDep,
)
from app.domains.shared.deps import AdminPermissionsDep, get_admin_user


router = APIRouter(prefix="/membership-types", tags=["Admin: Memberships"], dependencies=[Depends(get_admin_user)])


@router.get("")
async def get_membership_types(
    membership_type_service: MembershipTypeServiceDep,
    permissions: AdminPermissionsDep,
    filters: Annotated[MembershipTypesFilters, Depends()] = None,
) -> list[MembershipTypeSchema]:
    check_permissions("membership_types.view", permissions)
    return await membership_type_service.get_membership_types(
        filters=filters.model_dump(exclude_none=True),
        open_transaction=True,
    )


@router.get("/downgrade-requests", summary="Get all membership type change requests")
async def get_membership_type_change_requests(
    permissions: AdminPermissionsDep,
    use_case: GetMembershipDowngradeRequestsUseCaseDep,
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


@router.patch("/downgrade-requests/{request_id}", summary="Review membership type change request by ID")
async def review_membership_type_change_request(
    request_id: int,
    body: ReviewMembershipTypeChangeRequest,
    permissions: AdminPermissionsDep,
    use_case: ReviewMembershipDowngradeRequestUseCaseDep,
) -> ReviewedMembershipTypeChangeRequestSchema:
    return await use_case.execute(request_id, permissions, action=body.action, admin_comment=body.admin_comment)


@router.get("/{type_id}")
async def get_membership_type_detail(
    type_id: int,
    membership_type_service: MembershipTypeServiceDep,
    permissions: AdminPermissionsDep,
) -> MembershipTypeSchema:
    check_permissions("membership_types.view", permissions)
    return await membership_type_service.get_membership_type_by_id(membership_type_id=type_id, open_transaction=True)


@router.patch("/{type_id}")
async def update_membership_type(
    type_id: int,
    update_membership_data: UpdateMembershipTypeSchema,
    membership_type_service: MembershipTypeServiceDep,
    permissions: AdminPermissionsDep,
) -> MembershipTypeSchema:
    check_permissions("membership_types.update", permissions)
    return await membership_type_service.update_membership_type(
        type_id, open_transaction=True, **update_membership_data.model_dump(exclude_unset=True)
    )
