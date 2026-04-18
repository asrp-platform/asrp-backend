from typing import Annotated

from fastapi import Depends

from app.domains.shared.transaction_managers import TransactionManagerDep
from app.domains.users.models import User
from app.domains.users.services import UserServiceDep


class ChangeCurrentUserPasswordUseCase:
    def __init__(self, transaction_manager, service):
        self.__transaction_manager = transaction_manager
        self.__service = service

    async def execute(self, current_user: User, new_password: str, old_password: str):
        async with self.__transaction_manager:
            return await self.__service.change_password(
                current_user.id,
                old_password=old_password,
                new_password=new_password,
            )


def get_use_case(
    transaction_manager: TransactionManagerDep,
    service: UserServiceDep,
) -> ChangeCurrentUserPasswordUseCase:
    return ChangeCurrentUserPasswordUseCase(transaction_manager, service)


ChangeCurrentUserPasswordUseCaseDep = Annotated[ChangeCurrentUserPasswordUseCase, Depends(get_use_case)]
