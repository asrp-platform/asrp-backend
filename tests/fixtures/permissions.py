from typing import Awaitable, Callable, Sequence

import pytest

from app.domains.permissions.models import Permission
from app.domains.shared.transaction_managers import TransactionManager
from app.domains.users.models import User

pytestmark = pytest.mark.anyio


PermissionFactory = Callable[[User], Awaitable[Sequence[Permission]]]


@pytest.fixture(scope="function")
async def permissions(test_transaction_manager: TransactionManager) -> list[Permission]:
    permissions, _ = await test_transaction_manager.permission_repository.list()
    return permissions


@pytest.fixture(scope="function")
async def user_permissions_factory(
    test_transaction_manager: TransactionManager,
    permissions: list[Permission],
) -> PermissionFactory:
    async def _factory(user: User):
        user_permissions = [{"permission_id": p.id, "user_id": user.id} for p in permissions]
        return await test_transaction_manager.user_permission_repository.bulk_create(user_permissions)

    return _factory


@pytest.fixture(scope="function")
async def admin_all_permissions(
    test_transaction_manager: TransactionManager, permissions: list[Permission], admin_user: User
) -> list[Permission]:
    user_permissions = [{"permission_id": p.id, "user_id": admin_user.id} for p in permissions]
    return await test_transaction_manager.user_permission_repository.bulk_create(user_permissions)
