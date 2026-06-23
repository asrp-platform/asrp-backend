from typing import Annotated

from fastapi import Depends

from app.core.common.exceptions import NotFoundError, PermissionDeniedError
from app.domains.shared.transaction_managers import TransactionManager, TransactionManagerDep
from app.domains.users.models import User
from app.domains.users.services import UserService, UserServiceDep


class BanUserUseCase:
    """Use case for banning a user."""

    def __init__(self, transaction_manager: TransactionManager, user_service: UserService) -> None:
        self.__transaction_manager = transaction_manager
        self.__user_service = user_service

    async def execute(
        self,
        user_id: int,
        admin: User,
        permissions: list[str],
        ban_reason: str,
    ) -> User:
        if admin.id == user_id:
            raise PermissionDeniedError("Don't have enough permissions")

        async with self.__transaction_manager:
            target_user = await self.__user_service.get_user_by_kwargs(id=user_id)
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

            return await self.__user_service.ban_user(user_id, ban_reason)


def get_ban_user_use_case(
    transaction_manager: TransactionManagerDep,
    user_service: UserServiceDep,
) -> BanUserUseCase:
    return BanUserUseCase(transaction_manager, user_service)


BanUserUseCaseDep = Annotated[BanUserUseCase, Depends(get_ban_user_use_case)]
