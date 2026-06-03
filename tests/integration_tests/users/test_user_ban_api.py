import pytest
from httpx import AsyncClient

from app.domains.shared.deps import create_refresh_token
from app.domains.users.models import User
from tests.fixtures.auth import AuthHeaders

pytestmark = pytest.mark.anyio


async def test_admin_can_ban_user(
    client: AsyncClient,
    admin_auth_headers: AuthHeaders,
    test_user: User,
) -> None:
    user_id = test_user.id
    ban_payload = {"ban_reason": "Spamming in chats"}

    response = await client.put(
        f"/api/admin/users/{user_id}/ban",
        headers=admin_auth_headers,
        json=ban_payload,
    )

    assert response.status_code == 200
    data = response.json()
    assert data["banned"] is True
    assert data["ban_reason"] == "Spamming in chats"


async def test_admin_can_unban_user(
    client: AsyncClient,
    admin_auth_headers: AuthHeaders,
    test_user: User,
) -> None:
    user_id = test_user.id
    await client.put(
        f"/api/admin/users/{user_id}/ban",
        headers=admin_auth_headers,
        json={"ban_reason": "Spamming in chats"},
    )

    response = await client.delete(
        f"/api/admin/users/{user_id}/ban",
        headers=admin_auth_headers,
    )

    assert response.status_code == 200
    data = response.json()
    assert data["banned"] is False
    assert data["ban_reason"] is None


async def test_banned_user_cannot_login(
    client: AsyncClient,
    admin_auth_headers: AuthHeaders,
    confirmed_user_with_data: tuple[User, dict],
) -> None:
    user, user_data = confirmed_user_with_data
    await client.put(
        f"/api/admin/users/{user.id}/ban",
        headers=admin_auth_headers,
        json={"ban_reason": "Violation of Terms"},
    )
    login_payload = {"email": user_data["email"], "password": user_data["password"]}

    response = await client.post(
        "/api/auth/login",
        json=login_payload,
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "User is banned: Violation of Terms"


async def test_banned_user_access_token_invalid(
    client: AsyncClient,
    admin_auth_headers: AuthHeaders,
    test_user: User,
    auth_headers: AuthHeaders,
) -> None:
    response_before = await client.get(
        "/api/users/current-user",
        headers=auth_headers,
    )
    assert response_before.status_code == 200

    await client.put(
        f"/api/admin/users/{test_user.id}/ban",
        headers=admin_auth_headers,
        json={"ban_reason": "Abuse"},
    )

    response_after = await client.get(
        "/api/users/current-user",
        headers=auth_headers,
    )

    assert response_after.status_code == 401
    assert response_after.json()["detail"] == "Invalid token"


async def test_banned_user_refresh_token_invalid(
    client: AsyncClient,
    admin_auth_headers: AuthHeaders,
    test_user: User,
) -> None:
    token = create_refresh_token({"email": test_user.email})
    await client.put(
        f"/api/admin/users/{test_user.id}/ban",
        headers=admin_auth_headers,
        json={"ban_reason": "Abuse"},
    )
    client.cookies.set("refresh_token", token)

    response = await client.post("/api/auth/refresh")

    assert response.status_code == 401
    assert response.json()["detail"] == "Refresh token is invalid"


async def test_non_admin_cannot_ban_unban_user(
    client: AsyncClient,
    auth_headers: AuthHeaders,
    test_user: User,
) -> None:
    response_ban = await client.put(
        f"/api/admin/users/{test_user.id}/ban",
        headers=auth_headers,
        json={"ban_reason": "I am not admin"},
    )

    response_unban = await client.delete(
        f"/api/admin/users/{test_user.id}/ban",
        headers=auth_headers,
    )

    assert response_ban.status_code == 403
    assert response_unban.status_code == 403


async def test_admin_cannot_ban_self(
    client: AsyncClient,
    admin_auth_headers: AuthHeaders,
    admin_user: User,
) -> None:
    self_id = admin_user.id
    ban_payload = {"ban_reason": "Banning myself"}

    response = await client.put(
        f"/api/admin/users/{self_id}/ban",
        headers=admin_auth_headers,
        json=ban_payload,
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "You cannot ban yourself"


async def test_admin_cannot_unban_self(
    client: AsyncClient,
    admin_auth_headers: AuthHeaders,
    admin_user: User,
) -> None:
    self_id = admin_user.id

    response = await client.delete(
        f"/api/admin/users/{self_id}/ban",
        headers=admin_auth_headers,
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "You cannot unban yourself"
