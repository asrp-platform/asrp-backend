import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.shared.transaction_managers import TransactionManager
from app.domains.users.models import User
from tests.fixtures.auth import AuthHeaders, UserFactory


pytestmark = pytest.mark.anyio


async def test_delete_current_user_soft_deletes_only_authenticated_user(
    client: AsyncClient,
    auth_headers: AuthHeaders,
    test_user: User,
    user_factory: UserFactory,
    test_session: AsyncSession,
    test_transaction_manager: TransactionManager,
) -> None:
    other_user = await user_factory()

    response = await client.delete("/api/users/current-user", headers=auth_headers)

    assert response.status_code == 204
    assert response.content == b""
    # Query the table directly: the repository intentionally hides deleted rows.
    deleted = await test_session.scalar(select(User._deleted).where(User.id == test_user.id))
    other_deleted = await test_session.scalar(select(User._deleted).where(User.id == other_user.id))
    assert deleted is True
    assert other_deleted is False
    async with test_transaction_manager:
        assert await test_transaction_manager.user_repository.get_by_email(test_user.email) is None
        assert await test_transaction_manager.user_repository.get_first_by_kwargs(id=test_user.id) is None


async def test_delete_current_user_requires_authentication(
    client: AsyncClient,
    test_user: User,
    test_session: AsyncSession,
) -> None:
    response = await client.delete("/api/users/current-user")

    assert response.status_code == 401
    assert await test_session.scalar(select(User._deleted).where(User.id == test_user.id)) is False


@pytest.mark.parametrize("method", ["get", "delete"])
async def test_deleted_user_cannot_reuse_access_token(
    client: AsyncClient,
    auth_headers: AuthHeaders,
    method: str,
) -> None:
    response = await client.delete("/api/users/current-user", headers=auth_headers)
    assert response.status_code == 204

    response = await client.request(method, "/api/users/current-user", headers=auth_headers)

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid token"


async def test_deleted_user_cannot_refresh_access_token(
    client: AsyncClient,
    auth_headers: AuthHeaders,
    refresh_token: dict[str, str],
) -> None:
    client.cookies.update(refresh_token)
    response = await client.delete("/api/users/current-user", headers=auth_headers)
    assert response.status_code == 204

    response = await client.post("/api/auth/refresh")

    assert response.status_code == 401
    assert response.json()["detail"] == "Refresh token is invalid"


async def test_deleted_user_cannot_login(
    client: AsyncClient,
    confirmed_user_with_data: tuple[User, dict],
) -> None:
    _, user_data = confirmed_user_with_data
    credentials = {"email": user_data["email"], "password": user_data["password"]}
    login_response = await client.post("/api/auth/login", json=credentials)
    assert login_response.status_code == 200
    headers = {"Authorization": f"Bearer {login_response.json()['access_token']}"}
    response = await client.delete("/api/users/current-user", headers=headers)
    assert response.status_code == 204

    response = await client.post("/api/auth/login", json=credentials)

    assert response.status_code == 401
    assert response.json()["detail"] == "Wrong credentials"
