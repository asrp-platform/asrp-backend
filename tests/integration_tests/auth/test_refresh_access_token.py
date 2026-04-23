import pytest
from faker import Faker
from httpx import AsyncClient

from app.domains.shared.deps import create_refresh_token
from app.domains.users.models import User
from tests.integration_tests.auth.utils import decode_jwt

pytestmark = pytest.mark.anyio


async def test_refresh_access_token(
    client: AsyncClient,
    refresh_token,
    auth_headers,
    test_user: User,
) -> None:
    response = await client.post(
        "api/auth/refresh",
        headers=auth_headers,
        cookies=refresh_token,
    )

    assert response.status_code == 200
    assert decode_jwt(response.json()["access_token"])["email"] == test_user.email


async def test_refresh_access_token_not_authorized(
    client: AsyncClient,
) -> None:
    response = await client.post(
        "api/auth/refresh",
    )

    assert response.status_code == 401


async def test_refresh_access_token_invalid_token(
    client: AsyncClient,
    faker: Faker,
    auth_headers,
) -> None:
    response = await client.post(
        "api/auth/refresh",
        headers=auth_headers,
        cookies={"refresh_token": faker.pystr()},
    )

    assert response.status_code == 401


async def test_refresh_access_token_invalid_token_payload(
    client: AsyncClient,
    faker: Faker,
    auth_headers,
) -> None:
    refresh_token = create_refresh_token({"email": faker.pystr()})
    response = await client.post(
        "api/auth/refresh",
        headers=auth_headers,
        cookies={"refresh_token": refresh_token},
    )

    assert response.status_code == 401
