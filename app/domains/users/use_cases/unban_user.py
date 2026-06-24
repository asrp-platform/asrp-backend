from typing import Annotated

from fastapi import Depends

from app.core.common.exceptions import NotFoundError, PermissionDeniedError
from app.domains.shared.transaction_managers import TransactionManagerDep
from app.domains.users.models import User
from app.domains.users.services import UserServiceDep


class UnbanUserUseCase:
    """Use case for unbanning a user."""

    def __init__(self, transaction_manager: TransactionManagerDep, user_service: UserServiceDep) -> None:
        self.__transaction_manager = transaction_manager
        self.__user_service = user_service

    async def execute(
        self,
        target_user_id: int,
        admin: User,
        permissions: list[str],
    ) -> User:
        if admin.id == target_user_id:
            raise PermissionDeniedError("Don't have enough permissions")

        async with self.__transaction_manager:
            target_user = await self.__user_service.get_user_by_kwargs(id=target_user_id)
            if target_user is None:
                raise NotFoundError()

            if target_user.superuser:
                raise PermissionDeniedError("Don't have enough permissions")

            if target_user.admin:
                if "admin.update" not in permissions:
                    raise PermissionDeniedError("Don't have enough permissions")
            else:
                if "users.update" not in permissions:
                    raise PermissionDeniedError("Don't have enough permissions")

            return await self.__user_service.unban_user(target_user_id)


UnbanUserUseCaseDep = Annotated[UnbanUserUseCase, Depends()]
