from typing import Annotated

from fastapi import Depends
from stripe import Event

from app.core.database.base_transaction_manager import BaseTransactionManager
from app.domains.memberships.models import MembershipRequestStatusEnum
from app.domains.memberships.services import MembershipService, MembershipServiceDep
from app.domains.shared.transaction_managers import TransactionManagerDep


class ProcessCheckoutSessionCompletedUseCase:
    def __init__(
        self,
        transaction_manager: BaseTransactionManager,
        membership_service: MembershipService,
    ) -> None:
        self.__transaction_manager = transaction_manager
        self.__membership_service = membership_service

    async def execute(self, event: Event):
        session = event.data.object
        metadata = session.metadata
        membership_request_id = metadata.membership_request_id
        payment_status = session.payment_status  # paid or unpaid

        async with self.__transaction_manager:
            if payment_status == "paid":
                await self.__membership_service.update_membership_request(
                    int(membership_request_id), status=MembershipRequestStatusEnum.PAID
                )
            elif payment_status == "unpaid":
                await self.__membership_service.update_membership_request(
                    int(membership_request_id), status=MembershipRequestStatusEnum.PAYMENT_PENDING
                )
            elif payment_status == "no_payment_required":
                pass


def get_use_case(
    transaction_manager: TransactionManagerDep,
    membership_service: MembershipServiceDep,
) -> ProcessCheckoutSessionCompletedUseCase:
    return ProcessCheckoutSessionCompletedUseCase(transaction_manager, membership_service)


ProcessCheckoutSessionCompletedUseCaseDep = Annotated[ProcessCheckoutSessionCompletedUseCase, Depends(get_use_case)]
