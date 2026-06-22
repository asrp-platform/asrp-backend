from typing import Annotated

from fastapi import Depends

from app.core.common.exceptions import NotFoundError
from app.core.storage.storage_factory import FileStorageDep
from app.domains.shared.transaction_managers import TransactionManagerDep
from app.domains.users.models import User
from app.domains.users.services import UserServiceDep


class GetUserByIdUseCase:
    def __init__(
        self,
        user_service: UserServiceDep,
        transaction_manager: TransactionManagerDep,
        file_storage: FileStorageDep,
    ):
        self.__tm = transaction_manager
        self.__user_service = user_service
        self.__file_storage = file_storage

    async def execute(self, permissions: list[str], user_id: int) -> User:
        # check_permissions("users.view", permissions)
        async with self.__tm:
            user = await self.__user_service.get_user_by_kwargs(id=user_id)
            if user is None:
                raise NotFoundError("User with provided ID not found")
            if user.avatar_path is not None:
                user.avatar_url = await self.__file_storage.get_file_url(user.avatar_path)
            return user


GetUserByIdUseCaseDep = Annotated[GetUserByIdUseCase, Depends(GetUserByIdUseCase)]
