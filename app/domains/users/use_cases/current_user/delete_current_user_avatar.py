from dataclasses import dataclass
from typing import Annotated

from fastapi import Depends

from app.core.common.base_use_case import BaseUseCase
from app.domains.users.infrastructure import UserTransactionManagerBase, get_user_unit_of_work
from app.domains.users.models import User
from app.domains.users.services import UserService, get_user_service


@dataclass
class DeleteCurrentUserAvatarRequest:
    current_user: User


class DeleteCurrentUserAvatarUseCase(BaseUseCase[DeleteCurrentUserAvatarRequest, None]):
    def __init__(self, uow, service):
        self.uow = uow
        self.service = service

    async def execute(self, request: DeleteCurrentUserAvatarRequest):
        async with self.uow:
            return await self.service.delete_user_avatar(request.current_user.id)


def get_delete_current_user_avatar_use_case(
    uow: Annotated[UserTransactionManagerBase, Depends(get_user_unit_of_work)],
    service: Annotated[UserService, Depends(get_user_service)],
) -> DeleteCurrentUserAvatarUseCase:
    return DeleteCurrentUserAvatarUseCase(uow, service)


DeleteCurrentUserAvatarUseCaseDep = Annotated[
    DeleteCurrentUserAvatarUseCase, Depends(get_delete_current_user_avatar_use_case)
]
