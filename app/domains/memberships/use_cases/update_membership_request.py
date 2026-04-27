from datetime import datetime, timezone
from typing import Annotated

from fastapi import Depends

from app.core.database.base_transaction_manager import BaseTransactionManager
from app.core.utils.permissions import check_permissions
from app.domains.memberships.models import MembershipRequest
from app.domains.memberships.services import MembershipService, MembershipServiceDep
from app.domains.permissions.models import Permission
from app.domains.shared.transaction_managers import TransactionManagerDep
from app.domains.users.models import User


class UpdateMembershipRequestByIdUseCase:
    def __init__(self, transaction_manager: BaseTransactionManager, membership_service: MembershipService):
        self.__transaction_manager = transaction_manager
        self.__membership_service = membership_service

    async def execute(
        self,
        membership_request_id: int,
        actor: User,
        permissions: list[Permission],
        **kwargs,
    ) -> MembershipRequest:
        async with self.__transaction_manager:
            check_permissions("memberships.update", permissions)
            return await self.__membership_service.update_membership_request(
                membership_request_id, reviewer_id=actor.id, reviewed_at=datetime.now(timezone.utc), **kwargs
            )


def get_use_case(
    transaction_manager: TransactionManagerDep, membership_service: MembershipServiceDep
) -> UpdateMembershipRequestByIdUseCase:
    return UpdateMembershipRequestByIdUseCase(transaction_manager, membership_service)


UpdateMembershipRequestByIdUseCaseDep = Annotated[UpdateMembershipRequestByIdUseCase, Depends(get_use_case)]
