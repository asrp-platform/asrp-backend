import pytest
from httpx import AsyncClient

from app.domains.shared.deps import create_refresh_token
from app.domains.shared.transaction_managers import TransactionManager
from app.domains.users.models import User
from tests.fixtures.auth import AuthHeaders, UserFactory

pytestmark = pytest.mark.anyio


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
    admin_user: User,
    test_user: User,
    test_transaction_manager: TransactionManager,
) -> None:
    await grant_permission_to_admin(test_transaction_manager, admin_user.id, "users.update")
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
    admin_user: User,
    test_user: User,
    test_transaction_manager: TransactionManager,
) -> None:
    await grant_permission_to_admin(test_transaction_manager, admin_user.id, "users.update")
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
    admin_user: User,
    confirmed_user_with_data: tuple[User, dict],
    test_transaction_manager: TransactionManager,
) -> None:
    await grant_permission_to_admin(test_transaction_manager, admin_user.id, "users.update")
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
    admin_user: User,
    test_user: User,
    auth_headers: AuthHeaders,
    test_transaction_manager: TransactionManager,
) -> None:
    response_before = await client.get(
        "/api/users/current-user",
        headers=auth_headers,
    )
    assert response_before.status_code == 200

    await grant_permission_to_admin(test_transaction_manager, admin_user.id, "users.update")
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
    admin_user: User,
    test_user: User,
    test_transaction_manager: TransactionManager,
) -> None:
    token = create_refresh_token({"email": test_user.email})
    await grant_permission_to_admin(test_transaction_manager, admin_user.id, "users.update")
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
    test_transaction_manager: TransactionManager,
) -> None:
    await grant_permission_to_admin(test_transaction_manager, admin_user.id, "admin.update")
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
    test_transaction_manager: TransactionManager,
) -> None:
    await grant_permission_to_admin(test_transaction_manager, admin_user.id, "admin.update")
    self_id = admin_user.id

    response = await client.delete(
        f"/api/admin/users/{self_id}/ban",
        headers=admin_auth_headers,
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "You cannot unban yourself"


async def test_admin_without_users_view_cannot_get_users(
    client: AsyncClient,
    admin_auth_headers: AuthHeaders,
) -> None:
    response = await client.get(
        "/api/admin/users",
        headers=admin_auth_headers,
    )
    assert response.status_code == 403
    assert response.json()["detail"] == "Don't have enough permissions"


async def test_admin_with_users_view_can_get_users(
    client: AsyncClient,
    admin_auth_headers: AuthHeaders,
    admin_user: User,
    test_transaction_manager: TransactionManager,
) -> None:
    await grant_permission_to_admin(test_transaction_manager, admin_user.id, "users.view")

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
    response = await client.put(
        f"/api/admin/users/{test_user.id}/ban",
        headers=admin_auth_headers,
        json={"ban_reason": "No permission"},
    )
    assert response.status_code == 403
    assert response.json()["detail"] == "Don't have enough permissions"


async def test_admin_without_admin_update_cannot_ban_admin(
    client: AsyncClient,
    admin_auth_headers: AuthHeaders,
    admin_user: User,
    user_factory: UserFactory,
    test_transaction_manager: TransactionManager,
) -> None:
    await grant_permission_to_admin(test_transaction_manager, admin_user.id, "users.update")
    other_admin = await user_factory(admin=True)

    response = await client.put(
        f"/api/admin/users/{other_admin.id}/ban",
        headers=admin_auth_headers,
        json={"ban_reason": "No admin.update"},
    )
    assert response.status_code == 403
    assert response.json()["detail"] == "Don't have enough permissions"


async def test_admin_with_admin_update_can_ban_admin(
    client: AsyncClient,
    admin_auth_headers: AuthHeaders,
    admin_user: User,
    user_factory: UserFactory,
    test_transaction_manager: TransactionManager,
) -> None:
    await grant_permission_to_admin(test_transaction_manager, admin_user.id, "admin.update")
    other_admin = await user_factory(admin=True)

    response = await client.put(
        f"/api/admin/users/{other_admin.id}/ban",
        headers=admin_auth_headers,
        json={"ban_reason": "I have admin.update"},
    )
    assert response.status_code == 200


async def test_cannot_ban_superadmin(
    client: AsyncClient,
    admin_auth_headers: AuthHeaders,
    admin_user: User,
    user_factory: UserFactory,
    test_transaction_manager: TransactionManager,
) -> None:
    await grant_permission_to_admin(test_transaction_manager, admin_user.id, "admin.update")
    superadmin = await user_factory(admin=True, superuser=True)

    response = await client.put(
        f"/api/admin/users/{superadmin.id}/ban",
        headers=admin_auth_headers,
        json={"ban_reason": "Banning superadmin"},
    )
    assert response.status_code == 403
    assert response.json()["detail"] == "You cannot ban the system administrator"


async def test_admin_can_update_user_role(
    client: AsyncClient,
    admin_auth_headers: AuthHeaders,
    admin_user: User,
    test_user: User,
    test_transaction_manager: TransactionManager,
) -> None:
    await grant_permission_to_admin(test_transaction_manager, admin_user.id, "users.update")
    await grant_permission_to_admin(test_transaction_manager, admin_user.id, "admin.create")

    response = await client.patch(
        f"/api/admin/users/{test_user.id}",
        headers=admin_auth_headers,
        json={"admin": True},
    )
    assert response.status_code == 200
    assert response.json()["admin"] is True
