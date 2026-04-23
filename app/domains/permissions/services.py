from datetime import datetime, timezone
from typing import Annotated

from fastapi import Depends
from loguru import logger
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.core.logging import PRIVILEGES_CHANNEL
from app.domains.permissions.models import Permission
from app.domains.shared.transaction_managers import TransactionManager, TransactionManagerDep
from app.domains.users.exceptions import UserNotFoundError
from app.domains.users.models import User

privileges_logger = logger.bind(channel=PRIVILEGES_CHANNEL)


class PermissionsService:
    def __init__(self, transaction_manager):
        self.transaction_manager: TransactionManager = transaction_manager

    async def get_all_permissions(self):
        async with self.transaction_manager:
            return await self.transaction_manager.permission_repository.list()

    async def get_permissions_by_ids(self, permissions_ids: list[int]):
        stmt = select(Permission).where(Permission.id.in_(permissions_ids))
        async with self.transaction_manager:
            data, count = await self.transaction_manager.permission_repository.list(stmt=stmt)
            return data

    async def get_user_permissions(self, user_id: int) -> list[Permission]:
        async with self.transaction_manager:
            select_user_stmt = (
                select(User)
                .options(selectinload(User.permissions))  # сразу подгружаем
                .where(User.id == user_id)
            )
            user: User | None = (await self.transaction_manager._session.execute(select_user_stmt)).scalar_one_or_none()

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

        async with self.transaction_manager:
            request_time_utc = datetime.now(timezone.utc).isoformat()

            user_stmt = select(User).options(selectinload(User.permissions)).where(User.id == user_id)
            user: User | None = (await self.transaction_manager._session.execute(user_stmt)).scalar_one_or_none()

            if user is None:
                raise UserNotFoundError("User with provided ID not found")

            permissions_stmt = select(Permission).where(Permission.id.in_(permissions_ids))
            permissions = (await self.transaction_manager._session.execute(permissions_stmt)).scalars().all()
            user.permissions = permissions

            await self.transaction_manager._session.commit()

            privileges_logger.info(
                f"Admin: {actor.id} ({actor.email}) | Target: {user.id} ({user.email}) | New Permissions: {[p.action for p in permissions]} | Time: {request_time_utc}"
            )

            return user.permissions


def get_permissions_service(
    transaction_manager: TransactionManagerDep,
) -> PermissionsService:
    return PermissionsService(transaction_manager)


PermissionServiceDep = Annotated[PermissionsService, Depends(get_permissions_service)]
