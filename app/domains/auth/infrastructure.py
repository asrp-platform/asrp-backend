from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database.base_repository import SQLAlchemyRepository
from app.core.database.base_transaction_manager import SQLAlchemyTransactionManagerBase
from app.core.database.setup_db import session_getter
from app.domains.permissions.models import Permission, UserPermission
from app.domains.users.repositories import UserRepository


class PermissionRepository(SQLAlchemyRepository):
    model = Permission


class UserPermissionRepository(SQLAlchemyRepository):
    model = UserPermission


class AuthTransactionManagerBase(SQLAlchemyTransactionManagerBase):
    def __init__(self, session=None):
        super().__init__(session)
        self.user_repository = UserRepository(self._session)
        self.permission_repository = PermissionRepository(self._session)
        self.user_permission_repository = UserPermissionRepository(self._session)


def get_auth_unit_of_work(session: Annotated[AsyncSession, Depends(session_getter)]) -> AuthTransactionManagerBase:
    return AuthTransactionManagerBase(session)
