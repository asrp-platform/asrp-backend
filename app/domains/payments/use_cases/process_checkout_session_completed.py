from typing import Annotated

from fastapi import Depends
from stripe import Event

from app.domains.memberships.infrastructure import MembershipsTransactionManagerBase, get_memberships_unit_of_work
from app.domains.memberships.models import MembershipRequestStatusEnum
from app.domains.memberships.services import MembershipService, MembershipServiceDep


class ProcessCheckoutSessionCompletedUseCase:
    def __init__(
        self,
        uow: MembershipsTransactionManagerBase,
        membership_service: MembershipService,
    ) -> None:
        self.__uow = uow
        self.__membership_service = membership_service

    async def execute(self, event: Event):
        session = event.data.object
        metadata = session.metadata
        membership_request_id = metadata.membership_request_id
        payment_status = session.payment_status  # paid or unpaid

        async with self.__uow:
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
    uow: Annotated[MembershipsTransactionManagerBase, Depends(get_memberships_unit_of_work)],
    membership_service: MembershipServiceDep,
) -> ProcessCheckoutSessionCompletedUseCase:
    return ProcessCheckoutSessionCompletedUseCase(uow, membership_service)


ProcessCheckoutSessionCompletedUseCaseDep = Annotated[ProcessCheckoutSessionCompletedUseCase, Depends(get_use_case)]
