import asyncio
from typing import Annotated, Any

from fastapi import Depends

from app.core.storage.storage_factory import FileStorageDep
from app.domains.shared.transaction_managers import TransactionManagerDep
from app.domains.users.models import User


class GetMembersUseCase:
    def __init__(self, transaction_manager: TransactionManagerDep, file_storage: FileStorageDep):
        self.__tm = transaction_manager
        self.__file_storage = file_storage

    async def execute(
        self,
        *,
        limit: int,
        offset: int,
        order_by: str | None,
        filters: dict[str, Any],
    ) -> tuple[list[User], int]:
        async with self.__tm:
            members, count = await self.__tm.user_repository.list_active_members(
                limit=limit,
                offset=offset,
                order_by=order_by,
                **filters,
            )

        await asyncio.gather(*(self.__set_avatar_url(member) for member in members))
        return members, count

    async def __set_avatar_url(self, member: User) -> None:
        if member.avatar_path is not None:
            member.avatar_url = await self.__file_storage.get_file_url(member.avatar_path)


GetMembersUseCaseDep = Annotated[GetMembersUseCase, Depends(GetMembersUseCase)]
