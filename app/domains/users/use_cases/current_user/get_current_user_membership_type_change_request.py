from typing import Annotated

from fastapi import Depends

from app.domains.memberships.models import UserMembership, UserMembershipTypeChangeRequests
from app.domains.memberships.services import MembershipTypeChangeService, MembershipTypeChangeServiceDep
from app.domains.shared.transaction_managers import TransactionManager, TransactionManagerDep


class GetCurrentUserMembershipTypeChangeRequestUseCase:
    def __init__(
        self,
        transaction_manager: TransactionManager,
        membership_type_change_service: MembershipTypeChangeService,
    ):
        self.__transaction_manager = transaction_manager
        self.__membership_type_change_service = membership_type_change_service

    async def execute(self, current_user_membership: UserMembership) -> UserMembershipTypeChangeRequests | None:
        async with self.__transaction_manager:
            return await self.__membership_type_change_service.get_current_user_membership_type_change_request(
                current_user_membership
            )


def get_use_case(
    transaction_manager: TransactionManagerDep,
    membership_type_change_service: MembershipTypeChangeServiceDep,
) -> GetCurrentUserMembershipTypeChangeRequestUseCase:
    return GetCurrentUserMembershipTypeChangeRequestUseCase(transaction_manager, membership_type_change_service)


GetCurrentUserMembershipTypeChangeRequestUseCaseDep = Annotated[
    GetCurrentUserMembershipTypeChangeRequestUseCase, Depends(get_use_case)
]
