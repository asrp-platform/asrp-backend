from typing import Annotated, Any

from fastapi import Depends

from app.domains.payments.models import Payment, ProcessedWebhookEvent
from app.domains.shared.transaction_managers import TransactionManagerDep


class PaymentService:
    def __init__(self, transaction_manager):
        self.transaction_manager = transaction_manager

    async def create_payment(self, **kwargs) -> Payment:
        return await self.transaction_manager.payment_repository.create(**kwargs)

    async def update_payment(self, payment_id: int, **kwargs) -> Payment:
        return await self.transaction_manager.payment_repository.update(payment_id, **kwargs)

    async def get_payment_by_id(self, payment_uuid: str):
        return await self.transaction_manager.payment_repository.get_first_by_kwargs(id=payment_uuid)

    async def get_user_payments(
        self, user_id: int, limit: int = None, offset: int = None, order_by: str = None, filters: dict[str, Any] = None
    ) -> list[Payment]:
        # Can't use this method is use case when transaction manager used here
        async with self.transaction_manager:
            return await self.transaction_manager.payment_repository.list(
                limit=limit, offset=offset, order_by=order_by, filters={**filters, "user_id": user_id}
            )

    async def create_processed_webhook_event(self, **kwargs) -> ProcessedWebhookEvent:
        return await self.transaction_manager.processed_webhook_event_repository.create(**kwargs)

    async def get_processed_webhook_event_by_kwargs(self, **kwargs) -> ProcessedWebhookEvent:
        return await self.transaction_manager.processed_webhook_event_repository.get_first_by_kwargs(**kwargs)


def get_payment_service(transaction_manager: TransactionManagerDep) -> PaymentService:
    return PaymentService(transaction_manager)


PaymentServiceDep = Annotated[PaymentService, Depends(get_payment_service)]
