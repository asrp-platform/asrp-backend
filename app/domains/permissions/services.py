from datetime import datetime, timezone
from typing import Annotated

from fastapi import Depends
from loguru import logger
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.domains.permissions.infrastructure import PermissionsTransactionManagerBase, get_permissions_unit_of_work
from app.domains.permissions.models import Permission
from app.domains.users.exceptions import UserNotFoundError
from app.domains.users.models import User

privileges_logger = logger.bind(name="privileges")


class PermissionsService:
    def __init__(self, uow):
        self.uow: PermissionsTransactionManagerBase = uow

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
                raise UserNotFoundError("User with provided ID not found")
            return user.permissions

    async def set_users_permissions(self, user_id: int, permissions_ids: list[int], actor: User):
        """
        Set permissions for a user.

        Args:
            user_id (int): ID of the target user whose permissions will be updated.
            permissions_ids (list[int]): List of permission IDs to assign to the user.
            actor (User): The admin `User` performing the change (used for audit logging).

        Behavior:
            - Loads the target user and requested Permission objects.
            - Replaces the user's `permissions` collection with the permissions matching
              the provided `permissions_ids`.
            - Commits the transaction and writes an audit log entry.

        Returns:
            list[Permission]: The updated list of `Permission` objects assigned to the user.

        Raises:
            UserNotFoundError: If the target user is not found.
        """

        async with self.uow:
            request_time_utc = datetime.now(timezone.utc).isoformat()

            user_stmt = select(User).options(selectinload(User.permissions)).where(User.id == user_id)
            user: User | None = (await self.uow._session.execute(user_stmt)).scalar_one_or_none()

            if user is None:
                raise UserNotFoundError("User with provided ID not found")

            permissions_stmt = select(Permission).where(Permission.id.in_(permissions_ids))
            permissions = (await self.uow._session.execute(permissions_stmt)).scalars().all()
            user.permissions = permissions

            await self.uow._session.commit()

            privileges_logger.info(
                f"Admin: {actor.id} ({actor.email}) | Target: {user.id} ({user.email}) | New Permissions: {[p.action for p in permissions]} | Time: {request_time_utc}"
            )

            return user.permissions


def get_permissions_service(
    uow: Annotated[PermissionsTransactionManagerBase, Depends(get_permissions_unit_of_work)],
) -> PermissionsService:
    return PermissionsService(uow)


PermissionServiceDep = Annotated[PermissionsService, Depends(get_permissions_service)]
