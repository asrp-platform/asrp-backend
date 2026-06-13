from typing import Annotated, Any

from fastapi import Depends

from app.core.utils.permissions import check_permissions
from app.domains.memberships.models import UserMembership
from app.domains.memberships.services import UserMembershipServiceDep
from app.domains.shared.transaction_managers import TransactionManagerDep


class GetUsersWithMembershipsUseCase:
    def __init__(
        self,
        transaction_manager: TransactionManagerDep,
        user_membership_service: UserMembershipServiceDep,
    ):
        self.__tm = transaction_manager
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
        async with self.__tm:
            return await self.__user_membership_service.get_users_with_memberships(limit, offset, order_by, filters)


GetUsersWithMembershipsUseCaseDep = Annotated[GetUsersWithMembershipsUseCase, Depends(GetUsersWithMembershipsUseCase)]
