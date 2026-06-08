from typing import Annotated

from fastapi import Depends
from loguru import logger
from stripe import Event

from app.core.logging import PAYMENTS_CHANNEL
from app.domains.memberships.services import MembershipRequestServiceDep
from app.domains.payments.models import Payment, PaymentStatusEnum
from app.domains.payments.purpose_handlers.registry import PaymentPurposeHandlerRegistryDep
from app.domains.payments.services import PaymentServiceDep
from app.domains.shared.transaction_managers import TransactionManagerDep

payments_logger = logger.bind(channel=PAYMENTS_CHANNEL)


class ProcessPaymentUseCase:
    def __init__(
        self,
        transaction_manager: TransactionManagerDep,
        payment_service: PaymentServiceDep,
        membership_service: MembershipRequestServiceDep,
        payment_purpose_handler_registry: PaymentPurposeHandlerRegistryDep,
    ):
        self.__transaction_manager = transaction_manager
        self.__payment_service = payment_service
        self.__membership_service = membership_service
        self.__payment_purpose_handler_registry = payment_purpose_handler_registry

    async def execute(self, event: Event, target_payment_status: PaymentStatusEnum):
        payments_logger.info(
            "Processing payment event: event_id={} event_type={} target_status={}",
            event.id,
            event.type,
            target_payment_status.value,
        )

        metadata = event.data.object.metadata or {}
        payment_id = getattr(metadata, "payment_id", None)

        membership_request_id = getattr(metadata, "membership_request_id", None)

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
                    "Payment event skipped: missing payment_id in metadata, event_id={} event_type={} "
                    "membership_request_id={} ",
                    event.id,
                    event.type,
                    membership_request_id,
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
                    "Payment not found: payment is None, event_id={} payment_id={} status={}",
                    event.id,
                    payment_id,
                    target_payment_status.value,
                )
                await self.__payment_service.create_processed_webhook_event(
                    event_type=event.type,
                    event_id=event.id,
                    provider="STRIPE",
                )
                return

            if payment.status == target_payment_status:
                payments_logger.info(
                    "Payment event skipped: payment already has the target status, event_id={} payment_id={} status={}",
                    event.id,
                    payment_id,
                    target_payment_status.value,
                )
                await self.__payment_service.create_processed_webhook_event(
                    event_type=event.type,
                    event_id=event.id,
                    provider="STRIPE",
                )
                return

            if target_payment_status == PaymentStatusEnum.EXPIRED and payment.status != PaymentStatusEnum.PENDING:
                payments_logger.info(
                    "Payment expiration skipped: payment is not pending, event_id={} payment_id={} current_status={}",
                    event.id,
                    payment_id,
                    payment.status.value,
                )
                await self.__payment_service.create_processed_webhook_event(
                    event_type=event.type,
                    event_id=event.id,
                    provider="STRIPE",
                )
                return

            provider_data = self._construct_provider_data(payment, event)

            await self.__payment_service.update_payment(
                payment_id,
                status=target_payment_status,
                provider_data=provider_data,
            )

            await self.__payment_service.create_processed_webhook_event(
                event_type=event.type, event_id=event.id, provider="STRIPE"
            )

            payments_logger.info(
                "Payment updated: event_id={} payment_id={} status={}",
                event.id,
                payment_id,
                target_payment_status.value,
            )

            handler = self.__payment_purpose_handler_registry.get(payment.purpose)

            # Тут начинается логика в зависимости от payment_purpose
            if target_payment_status == PaymentStatusEnum.SUCCEEDED:
                await handler.on_succeeded(payment, event)

            elif target_payment_status == PaymentStatusEnum.FAILED:
                await handler.on_failed(payment, event)

            elif target_payment_status == PaymentStatusEnum.EXPIRED:
                await handler.on_expired(payment, event)

    @staticmethod
    def _construct_provider_data(payment: Payment, event: Event) -> dict:
        updated_provider_data = {**(payment.provider_data or {})}
        event_object = event.data.object

        if event.type.startswith("payment_intent."):
            updated_provider_data.update(
                {
                    "payment_intent_id": event_object.id,
                    "payment_intent_status": event_object.status,
                }
            )

        elif event.type.startswith("checkout.session."):
            updated_provider_data.update(
                {
                    "checkout_session_id": event_object.id,
                    "checkout_session_status": getattr(event_object, "status", None),
                    "checkout_session_payment_status": getattr(event_object, "payment_status", None),
                }
            )

        return updated_provider_data


ProcessPaymentUseCaseDep = Annotated[ProcessPaymentUseCase, Depends(ProcessPaymentUseCase)]
