from typing import Awaitable, Callable, Sequence

import pytest

from app.domains.permissions.infrastructure import PermissionsUnitOfWork
from app.domains.permissions.models import Permission
from app.domains.users.models import User

pytestmark = pytest.mark.anyio


PermissionFactory = Callable[[User], Awaitable[Sequence[Permission]]]


@pytest.fixture(scope="function")
async def permissions(permissions_uow: PermissionsUnitOfWork) -> list[Permission]:
    permissions, _ = await permissions_uow.permission_repository.list()
    return permissions


@pytest.fixture(scope="function")
async def user_permissions_factory(
    permissions_uow: PermissionsUnitOfWork,
    permissions: list[Permission],
) -> PermissionFactory:
    async def _factory(user: User):
        user_permissions = [{"permission_id": p.id, "user_id": user.id} for p in permissions]
        return await permissions_uow.user_permission_repository.bulk_create(user_permissions)

    return _factory
