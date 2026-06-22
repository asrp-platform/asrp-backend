from typing import Annotated, Any

from fastapi import Depends

from app.core.utils.permissions import check_permissions
from app.domains.shared.transaction_managers import TransactionManagerDep
from app.domains.users.models import User
from app.domains.users.services import UserServiceDep


class GetUsersUseCase:
    def __init__(
        self,
        user_service: UserServiceDep,
        transaction_manager: TransactionManagerDep,
    ):
        self.__tm = transaction_manager
        self.__user_service = user_service

    async def execute(
        self,
        permissions: list[str],
        *,
        limit: int = None,
        offset: int = None,
        order_by: str = None,
        filters: dict[str, Any] = None,
    ) -> [list[User], int]:
        check_permissions("feedback.view", permissions)
        async with self.__tm:
            return await self.__user_service.get_all_paginated_counted(limit, offset, order_by, filters)


GetUsersUseCaseDep = Annotated[GetUsersUseCase, Depends(GetUsersUseCase)]
