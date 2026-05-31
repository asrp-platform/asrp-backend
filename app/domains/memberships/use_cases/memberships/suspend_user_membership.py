from datetime import datetime

from app.core.common.exceptions import NotFoundError
from app.core.utils.permissions import check_permissions
from app.domains.memberships.exceptions import MembershipAlreadySuspendedError, MembershipAlreadyTerminatedError
from app.domains.memberships.services import UserMembershipServiceDep
from app.domains.shared.transaction_managers import TransactionManagerDep


class SuspendUserMembershipUseCase:
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
        membership_id: int,
        reason: str,
        suspended_until: datetime | None = None,
    ) -> None:
        check_permissions("memberships.update", permissions)

        async with self.__tm:
            membership = await self.__user_membership_service.get_user_membership_by_id(membership_id)
            if membership is None:
                raise NotFoundError("User membership with provided ID not found")
            if membership.terminated:
                # Обработать в эндпоинте
                raise MembershipAlreadyTerminatedError("User membership with provided ID already terminated")
            if membership.is_suspended:
                # Обработать в эндпоинте
                raise MembershipAlreadySuspendedError("User membership with provided ID already suspended")

            if suspended_until is None:
                await self.__user_membership_service.terminate_membership(
                    membership_id,
                    termination_reason=reason,
                )
            else:
                await self.__user_membership_service.suspend_membership(
                    membership_id,
                    suspended_until=suspended_until,
                    suspension_reason=reason,
                )
