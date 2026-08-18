from typing import Annotated

from fastapi import APIRouter, Depends

from app.core.common.request_params import OrderingParamsDep, PaginationParamsDep
from app.core.common.responses import InvalidRequestParamsResponses, NotAuthorizedResponses, PaginatedResponse
from app.domains.shared.deps import CurrentUserMembershipDep
from app.domains.users.filters import MembersFilter
from app.domains.users.schemas import MemberDirectorySchema
from app.domains.users.use_cases.member_directory.get_members import GetMembersUseCaseDep


router = APIRouter(prefix="/members", tags=["Membership: Members"])


class GetMembersResponses(InvalidRequestParamsResponses, NotAuthorizedResponses):
    NO_ACTIVE_MEMBERSHIP = 403, "No active membership"


@router.get("", summary="Get member directory", responses=GetMembersResponses.responses)
async def get_members(
    current_membership: CurrentUserMembershipDep,  # noqa: ARG001
    use_case: GetMembersUseCaseDep,
    params: PaginationParamsDep,
    ordering: OrderingParamsDep = None,
    filters: Annotated[MembersFilter, Depends()] = None,
) -> PaginatedResponse[MemberDirectorySchema]:
    data, count = await use_case.execute(
        limit=params["limit"],
        offset=params["offset"],
        order_by=ordering,
        filters=filters.model_dump(exclude_none=True),
    )
    return PaginatedResponse(
        count=count,
        page=params["page"],
        page_size=params["page_size"],
        data=data,
    )
