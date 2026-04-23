from typing import Annotated, Any

from fastapi import Depends

from app.core.database.base_transaction_manager import BaseTransactionManager
from app.core.utils.permissions import check_permissions
from app.domains.memberships.models import MembershipRequest
from app.domains.memberships.services import MembershipService, MembershipServiceDep
from app.domains.permissions.models import Permission
from app.domains.shared.transaction_managers import TransactionManagerDep


class GetMembershipRequestsAdminUseCase:
    def __init__(self, transaction_manager: BaseTransactionManager, membership_service: MembershipService):
        self.__transaction_manager = transaction_manager
        self.__membership_service = membership_service

    async def execute(
        self,
        permissions: list[Permission],
        limit: int = None,
        offset: int = None,
        order_by: str = None,
        filters: dict[str, Any] = None,
    ) -> [list[MembershipRequest], int]:
        check_permissions("memberships.view", permissions)
        async with self.__transaction_manager:
            return await self.__membership_service.get_membership_requests_paginated_counted(
                limit, offset, order_by, filters
            )


def get_use_case(
    transaction_manager: TransactionManagerDep, membership_service: MembershipServiceDep
) -> GetMembershipRequestsAdminUseCase:
    return GetMembershipRequestsAdminUseCase(transaction_manager, membership_service)


GetMembershipRequestsAdminUseCaseDep = Annotated[GetMembershipRequestsAdminUseCase, Depends(get_use_case)]
