from dataclasses import dataclass
from typing import Sequence

import pytest

from app.domains.permissions.models import Permission
from app.domains.users.models import User
from tests.fixtures.auth import AuthData, AuthFactory, UserFactory
from tests.fixtures.permissions import PermissionFactory


@dataclass
class UserContext:
    user: User
    auth: AuthData
    permissions: Sequence[Permission]


# Одна тяжеловесная фикстура админского контекста
@pytest.fixture(scope="function")
async def admin_all_permissions_context(
    user_factory: UserFactory,
    authentication_data_factory: AuthFactory,
    user_permissions_factory: PermissionFactory,
    permissions: list[Permission],
) -> UserContext:
    user = await user_factory(stuff=True)
    await user_permissions_factory(user)
    auth = authentication_data_factory(user)

    return UserContext(
        user=user,
        auth=auth,
        permissions=permissions,
    )


@pytest.fixture(scope="function")
async def admin_no_permissions_context(
    user_factory: UserFactory,
    authentication_data_factory: AuthFactory,
) -> UserContext:
    user = await user_factory(stuff=True)
    auth = authentication_data_factory(user)
    return UserContext(
        user=user,
        auth=auth,
        permissions=[],
    )


# Тяжеловесная фикстура пользовательского контекста
@pytest.fixture(scope="function")
async def user_context(
    user_factory: UserFactory,
    authentication_data_factory: AuthFactory,
    user_permissions_factory: PermissionFactory,
    permissions: list[Permission],
) -> UserContext:
    user = await user_factory()
    auth = authentication_data_factory(user)

    return UserContext(
        user=user,
        auth=auth,
        permissions=permissions,
    )
