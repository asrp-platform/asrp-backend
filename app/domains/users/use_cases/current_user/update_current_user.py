from typing import Annotated

from fastapi import Depends

from app.domains.shared.transaction_managers import TransactionManager, TransactionManagerDep
from app.domains.users.models import User
from app.domains.users.services import UserServiceDep


class UpdateCurrentUserUseCase:
    def __init__(self, transaction_manager: TransactionManager, user_service):
        self.__transaction_manager = transaction_manager
        self.__user_service = user_service

    async def execute(self, current_user: User, **kwargs):
        async with self.__transaction_manager:
            return await self.__user_service.update_user(user_id=current_user.id, **kwargs)


def get_use_case(
    transaction_manager: TransactionManagerDep,
    user_service: UserServiceDep,
) -> UpdateCurrentUserUseCase:
    return UpdateCurrentUserUseCase(transaction_manager, user_service)


UpdateCurrentUserUseCaseDep = Annotated[UpdateCurrentUserUseCase, Depends(get_use_case)]
