from typing import Annotated

from fastapi import Depends

from app.domains.payments.infrastructure import PaymentUnitOfWork, get_payment_unit_of_work


class PaymentService:
    def __init__(self, uow):
        self.uow: PaymentUnitOfWork = uow

    async def create_payment(self, **kwargs):
        return await self.uow.payment_repository.create(**kwargs)


def get_payment_service(
    uow: Annotated[PaymentUnitOfWork, Depends(get_payment_unit_of_work)],
) -> PaymentService:
    return PaymentService(uow)


PaymentServiceDep = Annotated[PaymentService, Depends(get_payment_service)]
