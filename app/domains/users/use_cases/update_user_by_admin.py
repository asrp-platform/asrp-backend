from typing import Annotated

from fastapi import Depends

from app.core.common.exceptions import NotFoundError, PermissionDeniedError
from app.core.utils.permissions import check_permissions
from app.domains.shared.transaction_managers import TransactionManagerDep
from app.domains.users.models import User
from app.domains.users.services import UserServiceDep


class UpdateUserByAdminUseCase:
    """Use case for updating user data by an administrator."""

    def __init__(self, transaction_manager: TransactionManagerDep, user_service: UserServiceDep) -> None:
        self.__transaction_manager = transaction_manager
        self.__user_service = user_service

    async def execute(
        self,
        target_user_id: int,
        admin: User,
        permissions: list[str],
        update_data: dict,
    ) -> User:
        async with self.__transaction_manager:
            target_user = await self.__user_service.get_user_by_kwargs(id=target_user_id)
            if target_user is None:
                raise NotFoundError()

            if target_user.admin:
                check_permissions("admin.update", permissions)
            else:
                check_permissions("users.update", permissions)

            is_admin_flag = update_data.get("admin")

            if is_admin_flag:
                check_permissions("admin.create", permissions)
            else:
                check_permissions("admin.delete", permissions)

            if is_admin_flag and admin.id == target_user_id:
                raise PermissionDeniedError("Don't have enough permissions")

            return await self.__user_service.update_user(target_user_id, **update_data)


UpdateUserByAdminUseCaseDep = Annotated[UpdateUserByAdminUseCase, Depends()]
