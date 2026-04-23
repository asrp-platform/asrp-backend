from typing import Annotated

from fastapi import Depends

from app.domains.shared.transaction_managers import TransactionManagerDep
from app.domains.users.models import User
from app.domains.users.services import UserServiceDep


class DeleteCurrentUserAvatarUseCase:
    def __init__(self, transaction_manager, user_service):
        self.__transaction_manager = transaction_manager
        self.__user_service = user_service

    async def execute(self, current_user: User):
        async with self.__transaction_manager:
            return await self.__user_service.delete_user_avatar(current_user.id)


def get_delete_current_user_avatar_use_case(
    transaction_manager: TransactionManagerDep,
    user_service: UserServiceDep,
) -> DeleteCurrentUserAvatarUseCase:
    return DeleteCurrentUserAvatarUseCase(transaction_manager, user_service)


DeleteCurrentUserAvatarUseCaseDep = Annotated[
    DeleteCurrentUserAvatarUseCase, Depends(get_delete_current_user_avatar_use_case)
]
