from typing import Annotated, Any

from fastapi import Depends
from stripe import Event

from app.core.database.base_transaction_manager import BaseTransactionManager
from app.domains.payments.models import PaymentStatusEnum
from app.domains.payments.services import PaymentService, PaymentServiceDep
from app.domains.shared.transaction_managers import TransactionManagerDep


def _get_metadata_value(metadata: Any, key: str) -> Any:
    if metadata is None:
        return None
    if isinstance(metadata, dict):
        return metadata.get(key)
    return getattr(metadata, key, None)


class ProcessCheckoutSessionExpiredUseCase:
    def __init__(
        self,
        transaction_manager: BaseTransactionManager,
        payment_service: PaymentService,
    ) -> None:
        self.__transaction_manager = transaction_manager
        self.__payment_service = payment_service

    async def execute(self, event: Event) -> None:
        checkout_session = event.data.object
        event_id = event.id
        event_type = event.type

        payment_id = _get_metadata_value(checkout_session.metadata, "payment_id")

        async with self.__transaction_manager:
            processed_webhook_event = await self.__payment_service.get_processed_webhook_event_by_kwargs(
                event_id=event_id,
            )
            if processed_webhook_event is not None:
                return

            if not payment_id:
                await self.__payment_service.create_processed_webhook_event(
                    event_type=event_type,
                    event_id=event_id,
                    provider="STRIPE",
                )
                return

            payment = await self.__payment_service.get_payment_by_id(payment_id)
            if payment is None:
                await self.__payment_service.create_processed_webhook_event(
                    event_type=event_type,
                    event_id=event_id,
                    provider="STRIPE",
                )
                return

            if payment.status == PaymentStatusEnum.PENDING:
                updated_provider_data = {
                    **(payment.provider_data or {}),
                    "checkout_session_id": checkout_session.id,
                    "checkout_session_payment_status": getattr(checkout_session, "payment_status", None),
                    "checkout_session_status": getattr(checkout_session, "status", None),
                }

                await self.__payment_service.update_payment(
                    payment_id,
                    status=PaymentStatusEnum.EXPIRED,
                    provider_data=updated_provider_data,
                )

            await self.__payment_service.create_processed_webhook_event(
                event_type=event_type,
                event_id=event_id,
                provider="STRIPE",
            )


def get_process_checkout_session_expired_use_case(
    transaction_manager: TransactionManagerDep,
    payment_service: PaymentServiceDep,
) -> ProcessCheckoutSessionExpiredUseCase:
    return ProcessCheckoutSessionExpiredUseCase(
        transaction_manager,
        payment_service,
    )


ProcessCheckoutSessionExpiredUseCaseDep = Annotated[
    ProcessCheckoutSessionExpiredUseCase,
    Depends(get_process_checkout_session_expired_use_case),
]
