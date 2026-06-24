from typing import Annotated

from fastapi import Depends

from app.core.common.exceptions import NotFoundError, PermissionDeniedError
from app.core.utils.permissions import check_permissions
from app.domains.shared.transaction_managers import TransactionManagerDep
from app.domains.users.models import User
from app.domains.users.services import UserServiceDep


class BanUserUseCase:
    """Use case for banning a user."""

    def __init__(self, transaction_manager: TransactionManagerDep, user_service: UserServiceDep) -> None:
        self.__transaction_manager = transaction_manager
        self.__user_service = user_service

    async def execute(
        self,
        target_user_id: int,
        admin: User,
        permissions: list[str],
        ban_reason: str,
    ) -> User:
        if admin.id == target_user_id:
            raise PermissionDeniedError("Don't have enough permissions")

        async with self.__transaction_manager:
            target_user = await self.__user_service.get_user_by_kwargs(id=target_user_id)
            if target_user is None:
                raise NotFoundError("User with provided ID not found")

            if target_user.superuser:
                raise PermissionDeniedError("Don't have enough permissions")

            if target_user.admin:
                check_permissions("admin.update", permissions)
            else:
                check_permissions("users.update", permissions)

            return await self.__user_service.ban_user(target_user_id, ban_reason)


BanUserUseCaseDep = Annotated[BanUserUseCase, Depends()]
