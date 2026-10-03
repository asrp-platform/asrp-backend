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
    confirmed_user_with_data: tuple[User, dict],
) -> None:
    _, user_data = confirmed_user_with_data

    response = await client.post(
        "api/auth/login",
        json={"email": user_data["email"], "password": user_data["password"]},
    )
    jwt_decoded = jwt.decode(response.json()["access_token"], settings.SECRET_KEY, algorithms=[settings.ALGORITHM])

    assert response.status_code == 200
    assert jwt_decoded["email"] == user_data["email"]


async def test_login_normalizes_email_case(
    client: AsyncClient,
    confirmed_user_with_data: tuple[User, dict],
) -> None:
    _, user_data = confirmed_user_with_data

    response = await client.post(
        "api/auth/login",
        json={"email": user_data["email"].upper(), "password": user_data["password"]},
    )

    assert response.status_code == 200
    assert (
        jwt.decode(response.json()["access_token"], settings.SECRET_KEY, algorithms=[settings.ALGORITHM])["email"]
        == (user_data["email"])
    )


async def test_login_normalizes_email_whitespace(
    client: AsyncClient,
    confirmed_user_with_data: tuple[User, dict],
) -> None:
    _, user_data = confirmed_user_with_data

    response = await client.post(
        "api/auth/login",
        json={"email": f"  {user_data['email']}  ", "password": user_data["password"]},
    )

    assert response.status_code == 200


async def test_access_token_expiry(
    client,
    confirmed_user_with_data: tuple[User, dict],
) -> None:
    _, user_data = confirmed_user_with_data

    response = await client.post(
        "/api/auth/login",
        json={
            "email": user_data["email"],
            "password": user_data["password"],
            "remember": False,
        },
    )

    payload = decode_jwt(response.json()["access_token"])

    exp = datetime.fromtimestamp(payload["exp"], tz=timezone.utc)
    now = datetime.now(timezone.utc)
    expected_delta = timedelta(minutes=settings.ACCESS_TOKEN_LIFESPAN_MINUTES)

    assert response.status_code == 200
    assert now + expected_delta - timedelta(seconds=5) <= exp <= now + expected_delta + timedelta(seconds=5)


async def test_refresh_token_expiry_with_remember_me(
    client,
    confirmed_user_with_data: tuple[User, dict],
) -> None:
    _, user_data = confirmed_user_with_data

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
    confirmed_user_with_data: tuple[User, dict],
) -> None:
    _, user_data = confirmed_user_with_data

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
    assert response.json()["detail"] == "Wrong credentials"


async def test_login_rejects_wrong_password(
    client: AsyncClient,
    confirmed_user_with_data: tuple[User, dict],
    faker: Faker,
) -> None:
    _, user_data = confirmed_user_with_data

    response = await client.post(
        "/api/auth/login",
        json={"email": user_data["email"], "password": faker.password()},
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Wrong credentials"


async def test_banned_user_cannot_login(
    client: AsyncClient,
    user_factory,
) -> None:
    password = "valid-password-123"
    user = await user_factory(pending=False, banned=True, ban_reason="Test ban", password=password)

    response = await client.post(
        "/api/auth/login",
        json={"email": user.email, "password": password},
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "User is banned"


async def test_pending_user_cannot_login(
    client: AsyncClient,
    test_user_with_data: tuple[User, dict],
) -> None:
    _, user_data = test_user_with_data

    response = await client.post(
        "/api/auth/login", json={"email": user_data["email"], "password": user_data["password"], "remember": True}
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Wrong credentials"
