import asyncio
from typing import Annotated, Any

from fastapi import Depends

from app.core.storage.storage_factory import FileStorageDep
from app.core.utils.permissions import check_permissions
from app.domains.shared.transaction_managers import TransactionManagerDep
from app.domains.users.models import User
from app.domains.users.services import UserServiceDep


class GetUsersUseCase:
    def __init__(
        self,
        user_service: UserServiceDep,
        transaction_manager: TransactionManagerDep,
        file_storage: FileStorageDep,
    ):
        self.__tm = transaction_manager
        self.__user_service = user_service
        self.__file_storage = file_storage

    async def execute(
        self,
        permissions: list[str],
        *,
        limit: int = None,
        offset: int = None,
        order_by: str = None,
        filters: dict[str, Any] = None,
    ) -> [list[User], int]:
        check_permissions("users.view", permissions)
        async with self.__tm:
            users, count = await self.__user_service.get_all_paginated_counted(limit, offset, order_by, filters)

            await asyncio.gather(*(self.__set_avatar_url(user) for user in users))

            return users, count

    async def __set_avatar_url(self, user: User) -> None:
        if user.avatar_path is None:
            return

        user.avatar_url = await self.__file_storage.get_file_url(user.avatar_path)


GetUsersUseCaseDep = Annotated[GetUsersUseCase, Depends(GetUsersUseCase)]
