from typing import Annotated, Any

from fastapi import Depends

from app.domains.payments.infrastructure import PaymentTransactionManagerBase, get_payment_unit_of_work
from app.domains.payments.models import Payment, ProcessedWebhookEvent


class PaymentService:
    def __init__(self, uow):
        self.uow: PaymentTransactionManagerBase = uow

    async def create_payment(self, **kwargs) -> Payment:
        return await self.uow.payment_repository.create(**kwargs)

    async def update_payment(self, payment_id: int, **kwargs) -> Payment:
        return await self.uow.payment_repository.update(payment_id, **kwargs)

    async def get_payment_by_id(self, payment_uuid: str):
        return await self.uow.payment_repository.get_first_by_kwargs(id=payment_uuid)

    async def get_user_payments(
        self, user_id: int, limit: int = None, offset: int = None, order_by: str = None, filters: dict[str, Any] = None
    ) -> list[Payment]:
        # нельзя использовать этот метод в use case, если здесь используется uow
        async with self.uow:
            return await self.uow.payment_repository.list(
                limit=limit, offset=offset, order_by=order_by, filters={**filters, "user_id": user_id}
            )

    async def create_processed_webhook_event(self, **kwargs) -> ProcessedWebhookEvent:
        return await self.uow.processed_webhook_event_repository.create(**kwargs)

    async def get_processed_webhook_event_by_kwargs(self, **kwargs) -> ProcessedWebhookEvent:
        return await self.uow.processed_webhook_event_repository.get_first_by_kwargs(**kwargs)


def get_payment_service(
    uow: Annotated[PaymentTransactionManagerBase, Depends(get_payment_unit_of_work)],
) -> PaymentService:
    return PaymentService(uow)


PaymentServiceDep = Annotated[PaymentService, Depends(get_payment_service)]
