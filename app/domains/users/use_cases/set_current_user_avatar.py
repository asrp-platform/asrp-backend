from dataclasses import dataclass
from typing import Annotated

from fastapi import Depends, File

from app.domains.memberships.use_cases.base import BaseUseCase
from app.domains.users.infrastructure import UserUnitOfWork, get_user_unit_of_work
from app.domains.users.models import User
from app.domains.users.services import UserService, get_user_service


@dataclass
class UploadCurrentUserAvatarRequest:
    current_user: User
    file: File


class UploadCurrentUserAvatarUseCase(BaseUseCase[UploadCurrentUserAvatarRequest, None]):
    def __init__(self, uow, service):
        self.uow = uow
        self.service = service

    async def execute(self, request: UploadCurrentUserAvatarRequest):
        async with self.uow:
            await self.service.upload_avatar(request.current_user.id, request.file)
            return await self.service.get_user_avatar_url(request.current_user.id)


def get_upload_current_user_avatar_use_case(
    uow: Annotated[UserUnitOfWork, Depends(get_user_unit_of_work)],
    service: Annotated[UserService, Depends(get_user_service)],
) -> UploadCurrentUserAvatarUseCase:
    return UploadCurrentUserAvatarUseCase(uow, service)


UploadCurrentUserAvatarUseCaseDep = Annotated[
    UploadCurrentUserAvatarUseCase, Depends(get_upload_current_user_avatar_use_case)
]
