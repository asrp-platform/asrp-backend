from typing import Annotated, Any

from fastapi import Depends

from app.core.utils.permissions import check_permissions
from app.domains.memberships.models import MembershipDowngradeRequest
from app.domains.memberships.services import MembershipDowngradeService, MembershipTypeChangeServiceDep
from app.domains.shared.transaction_managers import TransactionManager, TransactionManagerDep


class GetTypeChangeRequestsUseCase:
    def __init__(
        self,
        transaction_manager: TransactionManager,
        membership_type_change_service: MembershipDowngradeService,
    ):
        self.__transaction_manager = transaction_manager
        self.__membership_type_change_service = membership_type_change_service

    async def execute(
        self,
        permissions: list[str],
        limit: int = None,
        offset: int = None,
        order_by: str = None,
        filters: dict[str, Any] = None,
    ) -> [list[MembershipDowngradeRequest], int]:
        check_permissions("memberships.view", permissions)
        async with self.__transaction_manager:
            return await self.__membership_type_change_service.get_all_paginated_counted(
                limit, offset, order_by, filters
            )


def get_use_case(
    transaction_manager: TransactionManagerDep,
    membership_type_change_service: MembershipTypeChangeServiceDep,
) -> GetTypeChangeRequestsUseCase:
    return GetTypeChangeRequestsUseCase(transaction_manager, membership_type_change_service)


GetTypeChangeRequestsUseCaseDep = Annotated[GetTypeChangeRequestsUseCase, Depends(get_use_case)]
