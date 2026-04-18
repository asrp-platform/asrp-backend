from typing import Annotated

from fastapi import Depends

from app.domains.memberships.services import MembershipService, MembershipServiceDep
from app.domains.shared.transaction_managers import TransactionManager, TransactionManagerDep
from app.domains.users.models import User


class GetCurrentUserMembershipRequestUseCase:
    def __init__(self, transaction_manager: TransactionManager, membership_service: MembershipService):
        self.__transaction_manager = transaction_manager
        self.__membership_service = membership_service

    async def execute(self, current_user: User):
        async with self.__transaction_manager:
            return await self.__membership_service.get_user_membership_request(current_user.id)


def get_use_case(
    transaction_manager: TransactionManagerDep, membership_service: MembershipServiceDep
) -> GetCurrentUserMembershipRequestUseCase:
    return GetCurrentUserMembershipRequestUseCase(transaction_manager, membership_service)


GetCurrentUserMembershipRequestUseCaseDep = Annotated[GetCurrentUserMembershipRequestUseCase, Depends(get_use_case)]
