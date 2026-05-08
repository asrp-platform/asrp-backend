from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi_exception_responses import Responses

from app.core.common.request_params import OrderingParamsDep, PaginationParamsDep
from app.core.common.responses import PaginatedResponse
from app.domains.memberships.exceptions import MissingMembershipRequestPayment, MissingRejectingCommentError
from app.domains.memberships.filters import MembershipRequestsFilters
from app.domains.memberships.schemas import MembershipRequestUpdateAdminSchema, MembershipRequestViewSchema
from app.domains.memberships.use_cases.get_membership_request_by_id import GetMembershipRequestByIdUseCaseDep
from app.domains.memberships.use_cases.get_membership_requests_admin import GetMembershipRequestsAdminUseCaseDep
from app.domains.memberships.use_cases.review_membership_request import ReviewMembershipRequestUseCaseDep
from app.domains.shared.deps import AdminPermissionsDep, AdminUserDep

router = APIRouter(prefix="/membership-requests", tags=["Admin: Membership Requests"])


@router.get("", summary="Get paginated filtered and sorted membership requests list")
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


class GetMembershipRequestResponses(Responses):
    MEMBERSHIP_REQUEST_NOT_FOUND = 404, "Membership request with provided ID not found"


@router.get(
    "/{membership_request_id}",
    responses=GetMembershipRequestResponses.responses,
    summary="Get membership request by ID",
)
async def get_membership_request(
    membership_request_id: int,
    admin: AdminUserDep,
    permissions: AdminPermissionsDep,
    use_case: GetMembershipRequestByIdUseCaseDep,
) -> MembershipRequestViewSchema:
    return await use_case.execute(membership_request_id, admin, permissions)


class ReviewMembershipRequestResponses(GetMembershipRequestResponses):
    MISSING_MEMBERSHIP_REQUEST_PAYMENT = 409, "Can't review approve or reject unpaid membership request"
    MISSING_REJECTING_COMMENT = 422, "When status is REJECTED admin_comment must be provided"


@router.patch(
    "/{membership_request_id}",
    responses=ReviewMembershipRequestResponses.responses,
    summary="Updated membership request by ID",
)
async def review_membership_request(
    membership_request_id: int,
    body: MembershipRequestUpdateAdminSchema,
    admin: AdminUserDep,
    permissions: AdminPermissionsDep,
    use_case: ReviewMembershipRequestUseCaseDep,
):
    try:
        return await use_case.execute(membership_request_id, admin, permissions, **body.model_dump())
    except MissingMembershipRequestPayment:
        raise ReviewMembershipRequestResponses.MISSING_MEMBERSHIP_REQUEST_PAYMENT
    except MissingRejectingCommentError:
        raise ReviewMembershipRequestResponses.MISSING_REJECTING_COMMENT
