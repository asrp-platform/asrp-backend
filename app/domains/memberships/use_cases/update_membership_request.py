from datetime import datetime, timedelta, timezone
from typing import Annotated

from fastapi import Depends

from app.core.database.base_transaction_manager import BaseTransactionManager
from app.core.utils.permissions import check_permissions
from app.domains.memberships.models import MembershipRequest, MembershipRequestStatusEnum
from app.domains.memberships.services import (
    MembershipService,
    MembershipServiceDep,
    UserMembershipService,
    UserMembershipServiceDep,
)
from app.domains.payments.services import PaymentService, PaymentServiceDep
from app.domains.permissions.models import Permission
from app.domains.shared.transaction_managers import TransactionManagerDep
from app.domains.users.models import User


class UpdateMembershipRequestByIdUseCase:
    def __init__(
        self,
        transaction_manager: BaseTransactionManager,
        membership_service: MembershipService,
        user_membership_service: UserMembershipService,
        payment_service: PaymentService,
    ):
        self.__transaction_manager = transaction_manager
        self.__membership_service = membership_service
        self.__user_membership_service = user_membership_service
        self.__payment_service = payment_service

    async def execute(
        self,
        membership_request_id: int,
        actor: User,
        permissions: list[Permission],
        **kwargs,
    ) -> MembershipRequest | None:
        async with self.__transaction_manager:
            check_permissions("memberships.update", permissions)
            membership_request = await self.__membership_service.update_membership_request(
                membership_request_id, reviewer_id=actor.id, reviewed_at=datetime.now(timezone.utc), **kwargs
            )
            approval_status = kwargs.get("status")
            if approval_status == MembershipRequestStatusEnum.PAID:
                await self.__user_membership_service.create_user_membership(
                    user_id=membership_request.user_id,
                    expires_at=datetime.now(timezone.utc) + timedelta(days=365),
                    membership_request_id=membership_request.id,
                    membership_type_id=membership_request.membership_type_id,
                )
            elif approval_status == MembershipRequestStatusEnum.REJECTED:
                succeeded_membership_request_payment = (
                    await self.__payment_service.get_successful_user_membership_application_payment(
                        membership_request.user_id
                    )
                )
                if succeeded_membership_request_payment is None:
                    return

            return membership_request


def get_use_case(
    transaction_manager: TransactionManagerDep,
    membership_service: MembershipServiceDep,
    user_membership_service: UserMembershipServiceDep,
    payment_service: PaymentServiceDep,
) -> UpdateMembershipRequestByIdUseCase:
    return UpdateMembershipRequestByIdUseCase(
        transaction_manager, membership_service, user_membership_service, payment_service
    )


UpdateMembershipRequestByIdUseCaseDep = Annotated[UpdateMembershipRequestByIdUseCase, Depends(get_use_case)]
