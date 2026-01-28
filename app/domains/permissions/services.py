from typing import Annotated

from fastapi import Depends
from fastapi_exception_responses import Responses
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.domains.permissions.infrastructure import PermissionsUnitOfWork, get_permissions_unit_of_work
from app.domains.permissions.models import Permission
from app.domains.users.models import User


class RegisterResponses(Responses):
    PASSWORDS_DONT_MATCH = 400, "Passwords don't match"
    EMAIL_ALREADY_IN_USE = 409, "Provided email is already in use"


class PermissionsService:
    def __init__(self, uow):
        self.uow: PermissionsUnitOfWork = uow

    async def get_all_permissions(self):
        async with self.uow:
            return await self.uow.permission_repository.list()

    async def get_permissions_by_ids(self, permissions_ids: list[int]):
        stmt = select(Permission).where(Permission.id.in_(permissions_ids))
        async with self.uow:
            data, count = await self.uow.permission_repository.list(stmt=stmt)
            return data

    async def get_user_permissions(self, user_id: int) -> list[Permission]:
        async with self.uow:
            select_user_stmt = (
                select(User)
                .options(selectinload(User.permissions))  # сразу подгружаем
                .where(User.id == user_id)
            )
            user: User | None = (await self.uow._session.execute(select_user_stmt)).scalar_one_or_none()

            if user is None:
                raise ValueError("User with provided ID not found")

            return user.permissions

    async def assign_permissions_to_user(self, user_id: int, permissions_ids: list[int]):
        async with self.uow:
            select_user_stmt = (
                select(User)
                .options(selectinload(User.permissions))  # сразу подгружаем
                .where(User.id == user_id)
            )
            user: User | None = (await self.uow._session.execute(select_user_stmt)).scalar_one_or_none()

            if user is None:
                raise ValueError("User with provided ID not found")

            select_permissions_stmt = select(Permission).where(Permission.id.in_(permissions_ids))
            permissions = (await self.uow._session.execute(select_permissions_stmt)).scalars().all()

            existing_ids = {p.id for p in user.permissions}
            new_permissions = [p for p in permissions if p.id not in existing_ids]

            user.permissions.extend(new_permissions)
            await self.uow._session.commit()

    async def remove_permissions_from_user(self, user_id: int, permissions_ids: list[int]):
        async with self.uow:
            select_user_stmt = (
                select(User)
                .options(selectinload(User.permissions))  # сразу подгружаем
                .where(User.id == user_id)
            )
            user: User | None = (await self.uow._session.execute(select_user_stmt)).scalar_one_or_none()

            if user is None:
                raise ValueError("User with provided ID not found")

            select_permissions_stmt = select(Permission).where(Permission.id.in_(permissions_ids))
            permissions = (await self.uow._session.execute(select_permissions_stmt)).scalars().all()

            existing_ids = {p.id for p in user.permissions}
            permissions_to_delete = [p for p in permissions if p.id in existing_ids]

            for p in permissions_to_delete:
                if p in user.permissions:
                    user.permissions.remove(p)

    async def set_users_permissions(self, user_id: int, permissions_ids):
        async with self.uow:
            user_stmt = select(User).options(selectinload(User.permissions)).where(User.id == user_id)
            user: User | None = (await self.uow._session.execute(user_stmt)).scalar_one_or_none()

            if user is None:
                raise ValueError("User with provided ID not found")

            permissions_stmt = select(Permission).where(Permission.id.in_(permissions_ids))
            permissions = (await self.uow._session.execute(permissions_stmt)).scalars().all()
            user.permissions = permissions

            await self.uow._session.commit()
            return user.permissions


def get_permissions_service(
    uow: Annotated[PermissionsUnitOfWork, Depends(get_permissions_unit_of_work)],
) -> PermissionsService:
    return PermissionsService(uow)


PermissionServiceDep = Annotated[PermissionsService, Depends(get_permissions_service)]
