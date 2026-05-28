from typing import Annotated

from fastapi import Depends

from app.domains.memberships.models import MembershipDowngradeRequest, UserMembership
from app.domains.memberships.services import MembershipDowngradeService, MembershipTypeChangeServiceDep
from app.domains.shared.transaction_managers import TransactionManager, TransactionManagerDep


class GetCurrentUserMembershipDowngradeRequestUseCase:
    def __init__(
        self,
        transaction_manager: TransactionManager,
        membership_type_change_service: MembershipDowngradeService,
    ):
        self.__transaction_manager = transaction_manager
        self.__membership_type_change_service = membership_type_change_service

    async def execute(self, current_user_membership: UserMembership) -> MembershipDowngradeRequest | None:
        async with self.__transaction_manager:
            return await self.__membership_type_change_service.get_current_user_membership_type_change_request(
                current_user_membership
            )


def get_use_case(
    transaction_manager: TransactionManagerDep,
    membership_type_change_service: MembershipTypeChangeServiceDep,
) -> GetCurrentUserMembershipDowngradeRequestUseCase:
    return GetCurrentUserMembershipDowngradeRequestUseCase(transaction_manager, membership_type_change_service)


GetCurrentUserMembershipDowngradeRequestUseCaseDep = Annotated[
    GetCurrentUserMembershipDowngradeRequestUseCase, Depends(get_use_case)
]
