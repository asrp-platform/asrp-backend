from typing import Annotated

from fastapi import Depends

from app.core.storage.storage_factory import FileStorageDep
from app.domains.shared.transaction_managers import TransactionManagerDep
from app.domains.users.models import User


class DeleteCurrentUserAvatarUseCase:
    def __init__(self, transaction_manager: TransactionManagerDep, file_storage: FileStorageDep):
        self._tm = transaction_manager
        self.file_storage = file_storage

    async def execute(self, current_user: User):
        async with self._tm:
            avatar_path = current_user.avatar_path
            await self._tm.user_repository.update(current_user.id, avatar_path=None)

            if avatar_path is not None:
                await self.file_storage.delete_file(avatar_path)


DeleteCurrentUserAvatarUseCaseDep = Annotated[DeleteCurrentUserAvatarUseCase, Depends()]
