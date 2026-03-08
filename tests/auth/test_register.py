from typing import Any

import pytest
from faker import Faker
from httpx import AsyncClient

from app.domains.auth.infrastructure import AuthUnitOfWork
from app.domains.users.infrastructure import UserUnitOfWork

pytestmark = pytest.mark.anyio


async def test_register(
    client: AsyncClient,
    auth_uow: AuthUnitOfWork,
    user_uow: UserUnitOfWork,
    user_registration_data,
) -> None:
    response = await client.post("api/auth/register", json=user_registration_data)
    user = await user_uow.user_repository.get_first_by_kwargs(email=user_registration_data["email"])

    assert response.status_code == 201
    assert user is not None


async def test_email_already_in_use(
    client: AsyncClient,
    auth_uow: AuthUnitOfWork,
    user_uow: UserUnitOfWork,
    user_data: dict[str | Any],
) -> None:
    user_creation_data = user_data.copy()

    await user_uow.user_repository.create(**user_creation_data)

    response = await client.post(
        "api/auth/register",
        json={
            **user_data,
            "repeat_password": user_data["password"],
        },
    )

    assert response.status_code == 409


async def test_password_dont_match(
    client: AsyncClient,
    faker: Faker,
    auth_uow: AuthUnitOfWork,
    user_registration_data,
) -> None:
    response = await client.post("api/auth/register", json={**user_registration_data, "repeat_password": faker.pystr()})

    user = await auth_uow.user_repository.get_first_by_kwargs(email=user_registration_data["email"])

    assert response.status_code == 422
    assert user is None
