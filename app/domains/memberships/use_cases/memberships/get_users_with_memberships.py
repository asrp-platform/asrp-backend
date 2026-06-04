from typing import Annotated, Any

from fastapi import Depends

from app.core.utils.permissions import check_permissions
from app.domains.memberships.models import UserMembership
from app.domains.memberships.services import UserMembershipService, UserMembershipServiceDep


class GetUsersWithMembershipsUseCase:
    def __init__(self, user_membership_service: UserMembershipService):
        self.__user_membership_service = user_membership_service

    async def execute(
        self,
        permissions: list[str],
        limit: int = None,
        offset: int = None,
        order_by: str = None,
        filters: dict[str, Any] = None,
    ) -> tuple[list[UserMembership], int]:
        check_permissions("memberships.view", permissions)
        return await self.__user_membership_service.get_users_with_memberships(limit, offset, order_by, filters)


def get_use_case(
    user_membership_service: UserMembershipServiceDep,
) -> GetUsersWithMembershipsUseCase:
    return GetUsersWithMembershipsUseCase(user_membership_service)


GetUsersWithMembershipsUseCaseDep = Annotated[GetUsersWithMembershipsUseCase, Depends(get_use_case)]
