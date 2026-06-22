from typing import Annotated

from fastapi import Depends

from app.core.common.exceptions import NotFoundError
from app.domains.shared.transaction_managers import TransactionManagerDep
from app.domains.users.models import User
from app.domains.users.services import UserServiceDep


class GetUserByIdUseCase:
    def __init__(
        self,
        user_service: UserServiceDep,
        transaction_manager: TransactionManagerDep,
    ):
        self.__tm = transaction_manager
        self.__user_service = user_service

    async def execute(self, permissions: list[str], user_id: int) -> User:
        # check_permissions("users.view", permissions)
        async with self.__tm:
            user = await self.__user_service.get_user_by_kwargs(id=user_id)
            if user is None:
                raise NotFoundError("User with provided ID not found")
            return user


GetUserByIdUseCaseDep = Annotated[GetUserByIdUseCase, Depends(GetUserByIdUseCase)]
