from typing import Annotated

from fastapi import Depends
from stripe import Event

from app.domains.memberships.models import MembershipRequestStatusEnum
from app.domains.memberships.services import MembershipServiceDep
from app.domains.payments.infrastructure import PaymentUOWDep
from app.domains.payments.models import PaymentStatusEnum
from app.domains.payments.services import PaymentService, PaymentServiceDep


class ProcessPaymentUseCase:
    def __init__(self, uow, payment_service: PaymentService, membership_service):
        self.__uow = uow
        self.__payment_service = payment_service
        self.__membership_service = membership_service

    async def execute(self, event: Event, payment_status: PaymentStatusEnum):
        payment_intent = event["data"]["object"]
        metadata = payment_intent.metadata
        payment_id = metadata.payment_id
        membership_request_id = metadata.membership_request_id
        if not payment_id:
            return

        async with self.__uow:
            processed_webhook_event = await self.__payment_service.get_processed_webhook_event_by_kwargs(
                event_id=event["id"],
            )

            if processed_webhook_event is not None:
                return

            if not payment_id:
                await self.__payment_service.create_processed_webhook_event(
                    event_type=event["type"],
                    event_id=event["id"],
                    provider="STRIPE",
                )
                return

            payment = await self.__payment_service.get_payment_by_id(payment_id)

            if payment.status == payment_status:
                await self.__payment_service.create_processed_webhook_event(
                    event_type=event["type"],
                    event_id=event["id"],
                    provider="STRIPE",
                )
                return

            updated_provider_data = {
                **(payment.provider_data or {}),  # defence from None
                "payment_intent_id": payment_intent.id,
                "payment_intent_status": payment_intent.status,
            }

            await self.__payment_service.update_payment(
                payment_id,
                status=payment_status,
                provider_data=updated_provider_data,
            )

            await self.__payment_service.create_processed_webhook_event(
                event_type=event["type"], event_id=event["id"], provider="STRIPE"
            )

            if payment_status == PaymentStatusEnum.FAILED:
                # Обновляю статус request'а, если платеж не прошел
                await self.__membership_service.update_membership_request(
                    int(membership_request_id), status=MembershipRequestStatusEnum.PAYMENT_FAILED
                )


def get_process_payment_use_case(
    uow: PaymentUOWDep,
    payment_service: PaymentServiceDep,
    membership_service: MembershipServiceDep,
) -> ProcessPaymentUseCase:
    return ProcessPaymentUseCase(uow, payment_service, membership_service)


ProcessPaymentUseCaseDep = Annotated[ProcessPaymentUseCase, Depends(get_process_payment_use_case)]
