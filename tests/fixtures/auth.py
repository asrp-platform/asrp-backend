from typing import Any, Awaitable, Callable

import pytest
from faker import Faker

from app.core.common.cryptographer import Cryptographer
from app.core.config import fernet
from app.domains.shared.deps import create_access_token, create_refresh_token
from app.domains.shared.transaction_managers import TransactionManager
from app.domains.users.models import User

pytestmark = pytest.mark.anyio


AuthData = tuple[dict[str, str], dict[str, str], User]
UserFactory = Callable[..., Awaitable[User]]
AuthFactory = Callable[[User], AuthData]

AuthHeaders = dict[str, str]


@pytest.fixture(scope="function")
async def user_factory(
    faker: Faker,
    test_transaction_manager: TransactionManager,
) -> UserFactory:
    async def _factory(**overrides) -> User:
        user_data = {
            "email": faker.email(),
            "password": faker.password(),
            "firstname": faker.first_name(),
            "lastname": faker.last_name(),
            "institution": faker.pystr(min_chars=2),
            "role": faker.pystr(min_chars=2),
            "country": faker.country(),
            "city": faker.city(),
            **overrides,
        }
        async with test_transaction_manager:
            return await test_transaction_manager.user_repository.create(**user_data)

    return _factory


# Existing user
# Три фикстуры снизу в при использовании одном тесте консистентны - относятся к одному юзеру
# Предназначены для аутентификации пользователя в эндпоинтах, требующих аутентификацию
@pytest.fixture
async def test_user(user_factory: UserFactory) -> User:
    return await user_factory()


@pytest.fixture
def auth_headers(test_user: User) -> AuthHeaders:
    access_token = create_access_token({"email": test_user.email})
    return {"Authorization": f"Bearer {access_token}"}


@pytest.fixture
def refresh_token(test_user: User):
    refresh_token = create_refresh_token(
        {"email": test_user.email},
        remember_me=False,
    )
    return {"refresh_token": refresh_token}


@pytest.fixture
async def admin_user(user_factory: UserFactory) -> User:
    return await user_factory(admin=True)


@pytest.fixture
def admin_auth_headers(admin_user: User):
    access_token = create_access_token({"email": admin_user.email})
    return {"Authorization": f"Bearer {access_token}"}


# User registration
@pytest.fixture(scope="function")
def user_registration_data(faker: Faker) -> dict[str, Any]:
    password = faker.password()
    return {
        "email": faker.email(),
        "password": password,
        "repeat_password": password,
        "firstname": faker.first_name(),
        "lastname": faker.last_name(),
        "institution": faker.pystr(min_chars=2),
        "role": faker.pystr(min_chars=2),
        "country": faker.country(),
        "city": faker.city(),
    }


@pytest.fixture(scope="function")
def user_data(user_registration_data) -> dict[str, Any]:
    user_data = user_registration_data.copy()
    user_data.pop("repeat_password")
    return user_data


@pytest.fixture(scope="function")
async def test_user_with_data(
    test_transaction_manager: TransactionManager,
    user_data: dict[str | Any],
) -> [User, dict]:
    user_creation_data = user_data.copy()
    user = await test_transaction_manager.user_repository.create(**user_creation_data)

    return user, user_data


@pytest.fixture(scope="function")
def cryptographer() -> Cryptographer:
    return Cryptographer(fernet)
