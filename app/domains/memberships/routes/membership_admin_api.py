from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi_exception_responses import Responses

from app.core.common.request_params import OrderingParamsDep, PaginationParamsDep
from app.core.common.responses import PaginatedResponse
from app.domains.memberships.exceptions import MembershipAlreadySuspendedError, MembershipAlreadyTerminatedError
from app.domains.memberships.filters import MembersFilters
from app.domains.memberships.schemas.membership_schemas import SuspendMembershipSchema, UserMembershipBoundedSchema
from app.domains.memberships.use_cases.memberships.get_users_with_memberships import GetUsersWithMembershipsUseCaseDep
from app.domains.memberships.use_cases.memberships.suspend_user_membership import SuspendUserMembershipUseCase
from app.domains.shared.deps import AdminPermissionsDep, get_admin_user


router = APIRouter(prefix="/memberships", tags=["Admin: Memberships"], dependencies=[Depends(get_admin_user)])


class MemberRestrictionsResponses(Responses):
    MEMBERSHIP_NOT_FOUND = 404, "User membership with provided ID not found"
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
