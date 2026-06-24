import pytest
from httpx import AsyncClient

from app.domains.shared.deps import create_access_token, create_refresh_token
from app.domains.shared.transaction_managers import TransactionManager
from app.domains.users.models import User
from tests.fixtures.auth import AuthHeaders, UserFactory


pytestmark = pytest.mark.anyio


@pytest.fixture
async def banned_user(user_factory: UserFactory) -> User:
    return await user_factory(banned=True, ban_reason="Violation of Terms")


async def grant_permission_to_admin(
    transaction_manager: TransactionManager,
    admin_id: int,
    action: str,
) -> None:
    async with transaction_manager:
        permission = await transaction_manager.permission_repository.get_first_by_kwargs(action=action)
        if permission:
            await transaction_manager.user_permission_repository.create(user_id=admin_id, permission_id=permission.id)


async def test_admin_can_ban_user(
    client: AsyncClient,
    admin_auth_headers: AuthHeaders,
    admin_all_permissions: list,
    test_user: User,
) -> None:
    response = await client.patch(
        f"/api/admin/users/{test_user.id}/ban",
        headers=admin_auth_headers,
        json={"ban_reason": "Spamming in chats"},
    )
    data = response.json()

    assert response.status_code == 200
    assert data["banned"] is True
    assert data["ban_reason"] == "Spamming in chats"


async def test_admin_can_unban_user(
    client: AsyncClient,
    admin_auth_headers: AuthHeaders,
    admin_all_permissions: list,
    banned_user: User,
) -> None:
    response = await client.delete(
        f"/api/admin/users/{banned_user.id}/ban",
        headers=admin_auth_headers,
    )
    data = response.json()

    assert response.status_code == 200
    assert data["banned"] is False
    assert data["ban_reason"] is None


async def test_banned_user_cannot_login(
    client: AsyncClient,
    user_factory: UserFactory,
) -> None:
    password = "SecretPassword123"
    user = await user_factory(banned=True, ban_reason="Violation of Terms", password=password, pending=False)

    response = await client.post(
        "/api/auth/login",
        json={"email": user.email, "password": password},
    )
    data = response.json()

    assert response.status_code == 403
    assert data["detail"] == "User is banned: Violation of Terms"


async def test_banned_user_access_token_invalid(
    client: AsyncClient,
    banned_user: User,
) -> None:
    access_token = create_access_token({"email": banned_user.email})
    headers = {"Authorization": f"Bearer {access_token}"}

    response = await client.get(
        "/api/users/current-user",
        headers=headers,
    )
    data = response.json()

    assert response.status_code == 401
    assert data["detail"] == "Invalid token"


async def test_banned_user_refresh_token_invalid(
    client: AsyncClient,
    banned_user: User,
) -> None:
    token = create_refresh_token({"email": banned_user.email})
    client.cookies.set("refresh_token", token)

    response = await client.post("/api/auth/refresh")
    data = response.json()

    assert response.status_code == 401
    assert data["detail"] == "Refresh token is invalid"


async def test_non_admin_cannot_ban_unban_user(
    client: AsyncClient,
    auth_headers: AuthHeaders,
    test_user: User,
) -> None:
    response_ban = await client.patch(
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
    admin_all_permissions: list,
) -> None:
    response = await client.patch(
        f"/api/admin/users/{admin_user.id}/ban",
        headers=admin_auth_headers,
        json={"ban_reason": "Banning myself"},
    )
    data = response.json()

    assert response.status_code == 403
    assert data["detail"] == "Don't have enough permissions"


async def test_admin_cannot_unban_self(
    client: AsyncClient,
    admin_auth_headers: AuthHeaders,
    admin_user: User,
    admin_all_permissions: list,
) -> None:
    response = await client.delete(
        f"/api/admin/users/{admin_user.id}/ban",
        headers=admin_auth_headers,
    )
    data = response.json()

    assert response.status_code == 403
    assert data["detail"] == "Don't have enough permissions"


async def test_admin_without_users_view_cannot_get_users(
    client: AsyncClient,
    admin_auth_headers: AuthHeaders,
) -> None:
    response = await client.get(
        "/api/admin/users",
        headers=admin_auth_headers,
    )

    assert response.status_code == 403


async def test_admin_with_users_view_can_get_users(
    client: AsyncClient,
    admin_auth_headers: AuthHeaders,
    admin_all_permissions: list,
) -> None:
    response = await client.get(
        "/api/admin/users",
        headers=admin_auth_headers,
    )

    assert response.status_code == 200


async def test_admin_without_users_update_cannot_ban_user(
    client: AsyncClient,
    admin_auth_headers: AuthHeaders,
    test_user: User,
) -> None:
    response = await client.patch(
        f"/api/admin/users/{test_user.id}/ban",
        headers=admin_auth_headers,
        json={"ban_reason": "No permission"},
    )

    assert response.status_code == 403


async def test_admin_without_admin_update_cannot_ban_admin(
    client: AsyncClient,
    admin_auth_headers: AuthHeaders,
    admin_user: User,
    user_factory: UserFactory,
    test_transaction_manager: TransactionManager,
) -> None:
    await grant_permission_to_admin(test_transaction_manager, admin_user.id, "users.update")
    other_admin = await user_factory(admin=True)

    response = await client.patch(
        f"/api/admin/users/{other_admin.id}/ban",
        headers=admin_auth_headers,
        json={"ban_reason": "No admin.update"},
    )

    assert response.status_code == 403


async def test_admin_with_admin_update_can_ban_admin(
    client: AsyncClient,
    admin_auth_headers: AuthHeaders,
    admin_all_permissions: list,
    user_factory: UserFactory,
) -> None:
    other_admin = await user_factory(admin=True)

    response = await client.patch(
        f"/api/admin/users/{other_admin.id}/ban",
        headers=admin_auth_headers,
        json={"ban_reason": "I have admin.update"},
    )

    assert response.status_code == 200


async def test_cannot_ban_superadmin(
    client: AsyncClient,
    admin_auth_headers: AuthHeaders,
    admin_all_permissions: list,
    user_factory: UserFactory,
) -> None:
    superadmin = await user_factory(admin=True, superuser=True)

    response = await client.patch(
        f"/api/admin/users/{superadmin.id}/ban",
        headers=admin_auth_headers,
        json={"ban_reason": "Banning superadmin"},
    )

    assert response.status_code == 403


async def test_admin_can_update_user_role(
    client: AsyncClient,
    admin_auth_headers: AuthHeaders,
    admin_all_permissions: list,
    test_user: User,
) -> None:
    response = await client.patch(
        f"/api/admin/users/{test_user.id}",
        headers=admin_auth_headers,
        json={"admin": True},
    )
    data = response.json()

    assert response.status_code == 200
    assert data["admin"] is True
