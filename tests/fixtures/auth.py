from typing import Any, Awaitable, Callable

import pytest
from faker import Faker

from app.core.common.cryptographer import Cryptographer
from app.core.config import fernet
from app.domains.shared.deps import create_access_token, create_refresh_token
from app.domains.users.infrastructure import UserUnitOfWork
from app.domains.users.models import User

pytestmark = pytest.mark.anyio


AuthData = tuple[dict[str, str], dict[str, str], str]
UserFactory = Callable[..., Awaitable[User]]
AuthFactory = Callable[[User], AuthData]


@pytest.fixture(scope="function")
async def user_factory(
    faker: Faker,
    user_uow: UserUnitOfWork,
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
        async with user_uow:
            return await user_uow.user_repository.create(**user_data)

    return _factory


@pytest.fixture(scope="function")
def authentication_data_factory() -> AuthFactory:
    def _factory(user: User) -> AuthData:
        access_token = create_access_token({"email": user.email})
        refresh_token = create_refresh_token(
            {"email": user.email},
            remember_me=False,
        )

        return (
            {"Authorization": f"Bearer {access_token}"},
            {"refresh_token": refresh_token},
            user.email,
        )

    return _factory


@pytest.fixture(scope="function")
async def user_authentication_data(user_factory: UserFactory, authentication_data_factory: AuthFactory) -> AuthData:
    user = await user_factory()
    return authentication_data_factory(user)


@pytest.fixture(scope="function")
def register_user_data(faker: Faker) -> dict[str, Any]:
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
def user_data(register_user_data: dict[str, Any]) -> dict[str, Any]:
    user_data = register_user_data.copy()
    user_data.pop("repeat_password")
    return user_data


@pytest.fixture(scope="function")
def cryptographer() -> Cryptographer:
    return Cryptographer(fernet)
