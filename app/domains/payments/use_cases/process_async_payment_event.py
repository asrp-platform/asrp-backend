from typing import Annotated

from fastapi import Depends
from stripe import Event

from app.domains.memberships.models import MembershipRequestStatusEnum
from app.domains.memberships.services import MembershipServiceDep
from app.domains.payments.infrastructure import PaymentUOWDep
from app.domains.payments.models import PaymentStatusEnum
from app.domains.payments.services import PaymentService, PaymentServiceDep


class ProcessCheckoutSessionAsyncPaymentUseCase:
    def __init__(self, uow, payment_service: PaymentService, membership_service):
        self.__uow = uow
        self.__payment_service = payment_service
        self.__membership_service = membership_service

    async def execute(self, event: Event) -> None:
        checkout_session = event["data"]["object"]
        event_type = event["type"]

        metadata = checkout_session.metadata or {}
        payment_id = metadata.payment_id
        membership_request_id_raw = metadata.membership_request_id

        if not payment_id:
            return

        try:
            membership_request_id = int(membership_request_id_raw) if membership_request_id_raw else None
        except (TypeError, ValueError):
            membership_request_id = None

        if event_type == "checkout.session.async_payment_succeeded":
            payment_status = PaymentStatusEnum.SUCCEEDED
            membership_request_status = MembershipRequestStatusEnum.PAID
        elif event_type == "checkout.session.async_payment_failed":
            payment_status = PaymentStatusEnum.FAILED
            membership_request_status = MembershipRequestStatusEnum.PAYMENT_FAILED
        else:
            return

        async with self.__uow:
            processed_webhook_event = await self.__payment_service.get_processed_webhook_event_by_kwargs(
                event_id=event["id"],
            )
            if processed_webhook_event is not None:
                return

            payment = await self.__payment_service.get_payment_by_id(payment_id)
            if payment is None:
                await self.__payment_service.create_processed_webhook_event(
                    event_type=event_type,
                    event_id=event["id"],
                    provider="STRIPE",
                )
                return

            updated_provider_data = {
                **(payment.provider_data or {}),
                "checkout_session_id": checkout_session.id,
                "checkout_session_payment_status": getattr(checkout_session, "payment_status", None),
                "checkout_session_status": getattr(checkout_session, "status", None),
            }

            await self.__payment_service.update_payment(
                payment_id,
                status=payment_status,
                provider_data=updated_provider_data,
            )

            if membership_request_id is not None:
                await self.__membership_service.update_membership_request(
                    membership_request_id,
                    status=membership_request_status,
                )

            await self.__payment_service.create_processed_webhook_event(
                event_type=event_type,
                event_id=event["id"],
                provider="STRIPE",
            )


def get_process_checkout_session_async_payment_use_case(
    uow: PaymentUOWDep,
    payment_service: PaymentServiceDep,
    membership_service: MembershipServiceDep,
) -> ProcessCheckoutSessionAsyncPaymentUseCase:
    return ProcessCheckoutSessionAsyncPaymentUseCase(
        uow,
        payment_service,
        membership_service,
    )


ProcessCheckoutSessionAsyncPaymentUseCaseDep = Annotated[
    ProcessCheckoutSessionAsyncPaymentUseCase,
    Depends(get_process_checkout_session_async_payment_use_case),
]
