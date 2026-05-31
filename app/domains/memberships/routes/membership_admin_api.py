from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi_exception_responses import Responses

from app.core.common.request_params import OrderingParamsDep, PaginationParamsDep
from app.core.common.responses import PaginatedResponse
from app.domains.memberships.exceptions import MembershipAlreadySuspendedError, MembershipAlreadyTerminatedError
from app.domains.memberships.filters import MembersFilters, UserMembershipTypeChangeRequestsFilters
from app.domains.memberships.schemas.membership_downgrade_schemas import (
    ReviewedMembershipTypeChangeRequestSchema,
    ReviewMembershipTypeChangeRequest,
    UserMembershipTypeChangeRequestViewSchema,
)
from app.domains.memberships.schemas.membership_schemas import SuspendMembershipSchema, UserMembershipBoundedSchema
from app.domains.memberships.use_cases.memberships.get_downgrade_requests import (
    GetMembershipDowngradeRequestsUseCaseDep,
)
from app.domains.memberships.use_cases.memberships.get_users_with_memberships import (
    GetUsersWithMembershipsUseCaseDep,
)
from app.domains.memberships.use_cases.memberships.review_downgrade_request import (
    ReviewMembershipDowngradeRequestUseCaseDep,
)
from app.domains.memberships.use_cases.memberships.suspend_user_membership import SuspendUserMembershipUseCase
from app.domains.shared.deps import AdminPermissionsDep, get_admin_user

router = APIRouter(prefix="/memberships", tags=["Admin: Memberships"], dependencies=[Depends(get_admin_user)])


class MemberRestrictionsResponses(Responses):
    MEMBERSHIP_ALREADY_TERMINATED = 409, "User membership with provided ID already terminated"
    MEMBERSHIP_ALREADY_SUSPEND = 409, "User membership with provided ID already suspended"


@router.post(
    "/{membership_id}/restrictions",
    status_code=201,
    responses=MemberRestrictionsResponses.responses,
    summary="Suspend user membership",
)
async def suspend_user_membership(
    permissions: AdminPermissionsDep,
    membership_id: int,
    body: SuspendMembershipSchema,
    use_case: Annotated[SuspendUserMembershipUseCase, Depends()],
) -> None:
    try:
        await use_case.execute(permissions, membership_id, reason=body.reason, suspended_until=body.suspended_until)
    except MembershipAlreadyTerminatedError:
        raise MemberRestrictionsResponses.MEMBERSHIP_ALREADY_TERMINATED
    except MembershipAlreadySuspendedError:
        raise MemberRestrictionsResponses.MEMBERSHIP_ALREADY_SUSPEND


@router.get("/members")
async def get_all_members(
    permissions: AdminPermissionsDep,
    use_case: GetUsersWithMembershipsUseCaseDep,
    params: PaginationParamsDep,
    ordering: OrderingParamsDep = None,
    filters: Annotated[MembersFilters, Depends()] = None,
) -> PaginatedResponse[UserMembershipBoundedSchema]:
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


@router.get("/types/downgrade-requests", summary="Get all membership type change requests")
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


@router.patch("/types/downgrade-requests/{request_id}", summary="Review membership type change request by ID")
async def review_membership_type_change_request(
    request_id: int,
    body: ReviewMembershipTypeChangeRequest,
    permissions: AdminPermissionsDep,
    use_case: ReviewMembershipDowngradeRequestUseCaseDep,
) -> ReviewedMembershipTypeChangeRequestSchema:
    return await use_case.execute(request_id, permissions, action=body.action, admin_comment=body.admin_comment)
