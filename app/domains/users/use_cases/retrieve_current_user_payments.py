from typing import Annotated, Any

from fastapi import Depends

from app.core.database.unit_of_work import SQLAlchemyUnitOfWork
from app.domains.payments.infrastructure import PaymentUnitOfWork, get_payment_unit_of_work
from app.domains.payments.services import PaymentServiceDep
from app.domains.users.models import User


class RetrieveCurrentUserPaymentsUseCase:
    def __init__(self, uow: SQLAlchemyUnitOfWork, payment_service: PaymentServiceDep):
        self.__payment_service = payment_service
        self.__uow = uow

    async def execute(
        self,
        current_user: User,
        limit: int = None,
        offset: int = None,
        order_by: str = None,
        filters: dict[str, Any] = None,
    ):
        async with self.__uow:
            return await self.__payment_service.get_user_payments(
                user_id=current_user.id, limit=limit, offset=offset, order_by=order_by, filters=filters
            )


def get_retrieve_current_user_payments_use_case(
    payment_service: PaymentServiceDep,
    uow: Annotated[PaymentUnitOfWork, Depends(get_payment_unit_of_work)],
) -> RetrieveCurrentUserPaymentsUseCase:
    return RetrieveCurrentUserPaymentsUseCase(uow, payment_service)


RetrieveCurrentUserPaymentsUseCaseDep = Annotated[
    RetrieveCurrentUserPaymentsUseCase, Depends(get_retrieve_current_user_payments_use_case)
]
