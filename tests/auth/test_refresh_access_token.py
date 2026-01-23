import pytest
from faker import Faker
from httpx import AsyncClient

from app.domains.shared.deps import create_refresh_token
from tests.auth.utils import decode_jwt

pytestmark = pytest.mark.anyio


async def test_refresh_access_token(
    client: AsyncClient,
    user_authentication_data,
) -> None:
    authorization_header, refresh_token_cookie, email = user_authentication_data

    response = await client.post(
        "api/auth/refresh",
        headers=authorization_header,
        cookies=refresh_token_cookie,
    )

    assert response.status_code == 200
    assert decode_jwt(response.json()["access_token"])["email"] == email


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
    user_authentication_data,
) -> None:
    authorization_header, _, email = user_authentication_data
    response = await client.post(
        "api/auth/refresh",
        headers=authorization_header,
        cookies={"refresh_token": faker.pystr()},
    )

    assert response.status_code == 401


async def test_refresh_access_token_invalid_token_payload(
    client: AsyncClient,
    faker: Faker,
    user_authentication_data,
) -> None:
    authorization_header, _, _ = user_authentication_data
    refresh_token = create_refresh_token({"email": faker.pystr()})
    response = await client.post(
        "api/auth/refresh",
        headers=authorization_header,
        cookies={"refresh_token": refresh_token},
    )

    assert response.status_code == 401
