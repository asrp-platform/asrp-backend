import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Annotated, Any

from fastapi import Depends

from app.core.config import BASE_DIR
from app.domains.users.exceptions import InvalidPasswordError
from app.domains.users.infrastructure import UserUnitOfWork, get_user_unit_of_work
from app.domains.users.models import User

"""
Не использую HTTPExceptions в сервисах, так как
это сделало бы сервисы зависимыми от фреймворка
"""


class UserService:
    def __init__(self, uow):
        self.uow = uow

    async def get_all_paginated_counted(
        self, limit: int = None, offset: int = None, order_by: str = None, filters: dict[str, Any] = None
    ) -> [list[User], int]:
        async with self.uow:
            return await self.uow.user_repository.list(limit, offset, order_by, filters)

    async def get_all_users_count(self) -> int:
        async with self.uow:
            return await self.uow.user_repository.get_count()

    async def create(self, **kwargs):
        async with self.uow:
            return await self.uow.user_repository.create(**kwargs)

    async def get_user_by_kwargs(self, **kwargs) -> User:
        async with self.uow:
            return await self.uow.user_repository.get_first_by_kwargs(**kwargs)

    async def set_user_avatar(self, user_id: int, avatar_path: Path):
        async with self.uow:
            user = await self.uow.user_repository.get_first_by_kwargs(id=user_id)
            if user is None:
                raise ValueError("There is no such user with provided id")
            try:
                os.remove(BASE_DIR / user.avatar_path)
            except Exception:
                # TODO: Залогировать ошибку
                pass

            await self.uow.user_repository.update(user_id, {"avatar_path": avatar_path})

    async def update_user(self, user_id: int, update_data: dict) -> User:
        async with self.uow:
            user = await self.uow.user_repository.get_first_by_kwargs(id=user_id)
            if user is None:
                raise ValueError("There is no such user with provided id")
            await self.uow.user_repository.update(user_id, update_data)
        return user

    async def delete_avatar(self, user_id: int) -> None:
        async with self.uow:
            user = await self.uow.user_repository.get_first_by_kwargs(id=user_id)
            if user is None:
                raise ValueError("There is no such user with provided id")
            os.remove(BASE_DIR / user.avatar_path)
            await self.uow.user_repository.update(user_id, {"avatar_path": None})

    async def change_password(self, user_id, old_password, new_password):
        async with self.uow:
            user = await self.uow.user_repository.get_first_by_kwargs(id=user_id)

            if user is None:
                raise ValueError("user with provided email not found")

            if not user.verify_password(old_password):
                raise InvalidPasswordError("Invalid password")

            user.password = new_password
            await self.uow._session.flush()  # noqa property's setter manual calling
            await self.uow.user_repository.update(user.id, {"last_password_change": datetime.now(tz=timezone.utc)})


def get_user_service(uow: Annotated[UserUnitOfWork, Depends(get_user_unit_of_work)]) -> UserService:
    return UserService(uow)


UserServiceDep = Annotated[UserService, Depends(get_user_service)]
