from typing import Annotated

from fastapi import Depends, File

from app.domains.shared.transaction_managers import TransactionManagerDep
from app.domains.users.models import User
from app.domains.users.services import UserServiceDep


class UploadCurrentUserAvatarUseCase:
    def __init__(self, transaction_manager, service):
        self.__transaction_manager = transaction_manager
        self.__service = service

    async def execute(self, current_user: User, file: File):
        async with self.__transaction_manager:
            await self.__service.upload_avatar(current_user.id, file)
            return await self.__service.get_user_avatar_url(current_user.id)


def get_use_case(
    transaction_manager: TransactionManagerDep,
    service: UserServiceDep,
) -> UploadCurrentUserAvatarUseCase:
    return UploadCurrentUserAvatarUseCase(transaction_manager, service)


UploadCurrentUserAvatarUseCaseDep = Annotated[UploadCurrentUserAvatarUseCase, Depends(get_use_case)]
