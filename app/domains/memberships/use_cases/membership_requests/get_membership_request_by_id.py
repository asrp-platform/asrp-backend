from typing import Annotated

from fastapi import Depends

from app.core.common.exceptions import PermissionDeniedError
from app.core.database.base_transaction_manager import BaseTransactionManager
from app.core.utils.permissions import check_permissions
from app.domains.memberships.models import MembershipRequest
from app.domains.memberships.services import MembershipRequestService, MembershipRequestServiceDep
from app.domains.shared.transaction_managers import TransactionManagerDep
from app.domains.users.models import User


class GetMembershipRequestByIdUseCase:
    def __init__(self, transaction_manager: BaseTransactionManager, membership_service: MembershipRequestService):
        self.__transaction_manager = transaction_manager
        self.__membership_service = membership_service

    async def execute(
        self,
        membership_request_id: int,
        actor: User,
        permissions: list[str],
    ) -> MembershipRequest:
        async with self.__transaction_manager:
            membership_request = await self.__membership_service.get_membership_request_by_id(membership_request_id)

            if self.__can_view_as_admin(permissions):
                return membership_request

            if self.__can_view_as_owner(actor, membership_request):
                return membership_request

            raise PermissionDeniedError

    @staticmethod
    async def __can_view_as_admin(permissions: list[str]):
        try:
            check_permissions("memberships.view", permissions)
        except PermissionDeniedError:
            return False

        return True

    @staticmethod
    async def __can_view_as_owner(actor: User, membership_request: MembershipRequest):
        return actor.id == membership_request.user_id


def get_use_case(
    transaction_manager: TransactionManagerDep, membership_service: MembershipRequestServiceDep
) -> GetMembershipRequestByIdUseCase:
    return GetMembershipRequestByIdUseCase(transaction_manager, membership_service)


GetMembershipRequestByIdUseCaseDep = Annotated[GetMembershipRequestByIdUseCase, Depends(get_use_case)]
