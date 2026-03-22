from dataclasses import dataclass
from typing import Annotated

from fastapi import Depends

from app.domains.memberships.use_cases.base import BaseUseCase
from app.domains.users.infrastructure import UserUnitOfWork, get_user_unit_of_work
from app.domains.users.models import User
from app.domains.users.services import UserService, get_user_service


@dataclass
class ChangeCurrentUserPasswordRequest:
    current_user: User
    new_password: str
    old_password: str


class ChangeCurrentUserPasswordUseCase(BaseUseCase[ChangeCurrentUserPasswordRequest, None]):
    def __init__(self, uow, service):
        self.uow = uow
        self.service = service

    async def execute(self, request: ChangeCurrentUserPasswordRequest):
        async with self.uow:
            return await self.service.change_password(
                request.current_user.id,
                old_password=request.old_password,
                new_password=request.new_password,
            )


def get_delete_current_user_avatar_use_case(
    uow: Annotated[UserUnitOfWork, Depends(get_user_unit_of_work)],
    service: Annotated[UserService, Depends(get_user_service)],
) -> ChangeCurrentUserPasswordUseCase:
    return ChangeCurrentUserPasswordUseCase(uow, service)


ChangeCurrentUserPasswordUseCaseDep = Annotated[
    ChangeCurrentUserPasswordUseCase, Depends(get_delete_current_user_avatar_use_case)
]
