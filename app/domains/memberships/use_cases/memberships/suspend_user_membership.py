from datetime import datetime

from app.core.common.exceptions import NotFoundError
from app.core.utils.permissions import check_permissions
from app.domains.emails.common.messages import build_membership_suspended_html, build_membership_terminated_html
from app.domains.emails.email_queue import EmailQueueDep
from app.domains.memberships.exceptions import MembershipAlreadySuspendedError, MembershipAlreadyTerminatedError
from app.domains.memberships.models import UserMembership
from app.domains.memberships.services import UserMembershipServiceDep
from app.domains.shared.transaction_managers import TransactionManagerDep
from app.domains.users.models import User
from app.domains.users.services import UserServiceDep


class SuspendUserMembershipUseCase:
    def __init__(
        self,
        transaction_manager: TransactionManagerDep,
        user_membership_service: UserMembershipServiceDep,
        user_service: UserServiceDep,
        email_queue: EmailQueueDep,
    ):
        self.__tm = transaction_manager
        self.__user_membership_service = user_membership_service
        self.__user_service = user_service
        self.__email_queue = email_queue

    async def execute(
        self,
        permissions: list[str],
        membership_id: int,
        reason: str,
        suspended_until: datetime | None = None,
    ) -> None:
        check_permissions("memberships.update", permissions)

        async with self.__tm:
            membership: UserMembership = await self.__user_membership_service.get_user_membership_by_id(membership_id)
            if membership is None:
                raise NotFoundError("User membership with provided ID not found")
            if membership.terminated:
                raise MembershipAlreadyTerminatedError("User membership with provided ID already terminated")
            if membership.is_suspended and suspended_until is not None:
                raise MembershipAlreadySuspendedError("User membership with provided ID already suspended")

            user: User = await self.__user_service._get_user_by_kwargs(id=membership.user_id)
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

        if suspended_until is None:
            subject, body = build_membership_terminated_html(user.full_name, reason)
        else:
            subject, body = build_membership_suspended_html(user.full_name, reason)

        await self.__email_queue.send_email(to=user.email, subject=subject, body=body)
