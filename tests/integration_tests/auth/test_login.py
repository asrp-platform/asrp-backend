from datetime import datetime, timedelta, timezone

import pytest
from faker import Faker
from httpx import AsyncClient
from jose import jwt

from app.core.config import settings
from app.domains.users.models import User
from tests.integration_tests.auth.utils import decode_jwt

pytestmark = pytest.mark.anyio


async def test_login(
    client: AsyncClient,
    test_user_with_data: [User, dict],
) -> None:
    _, user_data = test_user_with_data

    response = await client.post(
        "api/auth/login",
        json={"email": user_data["email"], "password": user_data["password"]},
    )
    jwt_decoded = jwt.decode(response.json()["access_token"], settings.SECRET_KEY, algorithms=[settings.ALGORITHM])

    assert response.status_code == 200
    assert jwt_decoded["email"] == user_data["email"]


async def test_access_token_expiry(
    client,
    test_user_with_data: [User, dict],
) -> None:
    _, user_data = test_user_with_data

    response = await client.post(
        "/api/auth/login",
        json={
            "email": user_data["email"],
            "password": user_data["password"],
            "remember_me": False,
        },
    )

    payload = decode_jwt(response.json()["access_token"])

    exp = datetime.fromtimestamp(payload["exp"], tz=timezone.utc)
    now = datetime.now(timezone.utc)
    expected_delta = timedelta(hours=settings.ACCESS_TOKEN_LIFESPAN_HOURS)

    assert response.status_code == 200
    assert now + expected_delta - timedelta(seconds=5) <= exp <= now + expected_delta + timedelta(seconds=5)


async def test_refresh_token_expiry_with_remember_me(
    client,
    test_user_with_data: [User, dict],
) -> None:
    _, user_data = test_user_with_data

    response = await client.post(
        "/api/auth/login",
        json={
            "email": user_data["email"],
            "password": user_data["password"],
            "remember": True,
        },
    )

    payload = jwt.decode(response.json()["refresh_token"], settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    exp = datetime.fromtimestamp(payload["exp"], tz=timezone.utc)
    now = datetime.now(timezone.utc)
    expected_delta = timedelta(days=settings.REFRESH_TOKEN_REMEMBER_ME_LIFETIME_DAYS)

    assert response.status_code == 200
    assert now + expected_delta - timedelta(seconds=5) <= exp <= now + expected_delta + timedelta(seconds=5)


async def test_refresh_token_expiry(
    client,
    test_user_with_data: [User, dict],
) -> None:
    _, user_data = test_user_with_data

    response = await client.post(
        "/api/auth/login",
        json={
            "email": user_data["email"],
            "password": user_data["password"],
            "remember": False,
        },
    )

    payload = jwt.decode(response.json()["refresh_token"], settings.SECRET_KEY, algorithms=[settings.ALGORITHM])

    exp = datetime.fromtimestamp(payload["exp"], tz=timezone.utc)
    now = datetime.now(timezone.utc)
    expected_delta = timedelta(days=settings.REFRESH_TOKEN_LIFETIME_DAYS)

    assert now + expected_delta - timedelta(seconds=5) <= exp <= now + expected_delta + timedelta(seconds=5)


async def test_user_does_not_exist(
    client,
    faker: Faker,
) -> None:
    response = await client.post(
        "/api/auth/login",
        json={
            "email": faker.email(),
            "password": faker.pystr(),
        },
    )

    assert response.status_code == 401
