from typing import Annotated, Any

from fastapi import Depends

from app.domains.payments.services import PaymentServiceDep
from app.domains.shared.transaction_managers import TransactionManagerDep
from app.domains.users.models import User


class RetrieveCurrentUserPaymentsUseCase:
    def __init__(self, transaction_manager, payment_service: PaymentServiceDep):
        self.__transaction_manager = transaction_manager
        self.__payment_service = payment_service

    async def execute(
        self,
        current_user: User,
        limit: int = None,
        offset: int = None,
        order_by: str = None,
        filters: dict[str, Any] = None,
    ):
        async with self.__transaction_manager:
            return await self.__payment_service.get_user_payments(
                user_id=current_user.id, limit=limit, offset=offset, order_by=order_by, filters=filters
            )


def get_retrieve_current_user_payments_use_case(
    payment_service: PaymentServiceDep,
    transaction_manager: TransactionManagerDep,
) -> RetrieveCurrentUserPaymentsUseCase:
    return RetrieveCurrentUserPaymentsUseCase(transaction_manager, payment_service)


RetrieveCurrentUserPaymentsUseCaseDep = Annotated[
    RetrieveCurrentUserPaymentsUseCase, Depends(get_retrieve_current_user_payments_use_case)
]
