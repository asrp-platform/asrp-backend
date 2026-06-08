from typing import Annotated

from fastapi import Depends
from loguru import logger
from stripe import Event

from app.core.logging import PAYMENTS_CHANNEL
from app.domains.payments.purpose_handlers.registry import PaymentPurposeHandlerRegistryDep
from app.domains.payments.services import PaymentServiceDep
from app.domains.shared.transaction_managers import TransactionManagerDep

payments_logger = logger.bind(channel=PAYMENTS_CHANNEL)


class ProcessCheckoutSessionCompletedUseCase:
    def __init__(
        self,
        transaction_manager: TransactionManagerDep,
        payment_service: PaymentServiceDep,
        payment_purpose_handler_registry: PaymentPurposeHandlerRegistryDep,
    ) -> None:
        self.__transaction_manager = transaction_manager
        self.__payment_service = payment_service
        self.__payment_purpose_handler_registry = payment_purpose_handler_registry

    async def execute(self, event: Event):
        metadata = event.data.object.metadata or {}
        payment_id = getattr(metadata, "payment_id", None)

        async with self.__transaction_manager:
            processed_webhook_event = await self.__payment_service.get_processed_webhook_event_by_kwargs(
                event_id=event.id,
            )

            if processed_webhook_event is not None:
                payments_logger.info(
                    "Payment event skipped: already processed, event_id={} event_type={}", event.id, event.type
                )
                return

            if not payment_id:
                payments_logger.warning(
                    "Payment event skipped: missing payment_id in metadata, event_id={} event_type={}",
                    event.id,
                    event.type,
                )
                await self.__payment_service.create_processed_webhook_event(
                    event_type=event.type,
                    event_id=event.id,
                    provider="STRIPE",
                )
                return

            payment = await self.__payment_service.get_payment_by_id(payment_id)

            if payment is None:
                payments_logger.info(
                    "Payment not found: payment is None, event_id={} payment_id={}",
                    event.id,
                    payment_id,
                )
                await self.__payment_service.create_processed_webhook_event(
                    event_type=event.type,
                    event_id=event.id,
                    provider="STRIPE",
                )
                return

            handler = self.__payment_purpose_handler_registry.get(payment.purpose)

            await handler.on_checkout_session_completed(payment, event)

            await self.__payment_service.create_processed_webhook_event(
                event_type=event.type,
                event_id=event.id,
                provider="STRIPE",
            )


ProcessCheckoutSessionCompletedUseCaseDep = Annotated[
    ProcessCheckoutSessionCompletedUseCase, Depends(ProcessCheckoutSessionCompletedUseCase)
]
