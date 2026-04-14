from typing import Awaitable, Callable, Sequence

import pytest

from app.domains.permissions.infrastructure import PermissionsTransactionManagerBase
from app.domains.permissions.models import Permission
from app.domains.users.models import User

pytestmark = pytest.mark.anyio


PermissionFactory = Callable[[User], Awaitable[Sequence[Permission]]]


@pytest.fixture(scope="function")
async def permissions(permissions_uow: PermissionsTransactionManagerBase) -> list[Permission]:
    permissions, _ = await permissions_uow.permission_repository.list()
    return permissions


@pytest.fixture(scope="function")
async def user_permissions_factory(
    permissions_uow: PermissionsTransactionManagerBase,
    permissions: list[Permission],
) -> PermissionFactory:
    async def _factory(user: User):
        user_permissions = [{"permission_id": p.id, "user_id": user.id} for p in permissions]
        return await permissions_uow.user_permission_repository.bulk_create(user_permissions)

    return _factory


@pytest.fixture(scope="function")
async def admin_all_permissions(
    permissions_uow: PermissionsTransactionManagerBase, permissions: list[Permission], admin_user: User
) -> list[Permission]:
    user_permissions = [{"permission_id": p.id, "user_id": admin_user.id} for p in permissions]
    return await permissions_uow.user_permission_repository.bulk_create(user_permissions)
