from dataclasses import dataclass
from unittest.mock import AsyncMock

import pytest
from httpx import AsyncClient

from app.domains.permissions.services import get_permissions_service
from app.domains.shared.deps import get_users_permissions
from app.domains.users.routes.admin_users_api import ManagePermissionsResponses
from app.main import app

pytestmark = pytest.mark.anyio


@dataclass
class MockPermission:
    """Simple mock object for permission representation in tests."""

    id: int
    action: str
    name: str


@pytest.fixture(scope="function")
def mock_service() -> AsyncMock:
    """Mock PermissionsService for testing API endpoints without database calls."""
    return AsyncMock()


@pytest.fixture(scope="function")
def override_permissions_service(mock_service: AsyncMock) -> None:
    """Override permissions service dependency with mock."""
    app.dependency_overrides[get_permissions_service] = lambda: mock_service
    yield
    app.dependency_overrides.pop(get_permissions_service, None)


@pytest.fixture(scope="function")
def mock_permissions_with_update() -> None:
    """Override permissions check to allow 'permissions.update' action."""

    async def mock_get_all_permissions():
        return ["permissions.update"]

    app.dependency_overrides[get_users_permissions] = mock_get_all_permissions
    yield
    app.dependency_overrides.pop(get_users_permissions, None)


async def test_put_permissions_success(
    client: AsyncClient,
    mock_service: AsyncMock,
    override_permissions_service,
    mock_permissions_with_update,
    admin_user,
    admin_auth_headers,
    admin_all_permissions,
    user_factory,
) -> None:
    target_user = await user_factory()
    new_perms_ids = [1, 2, 3]

    mock_permissions = [
        MockPermission(id=1, action="admin.create", name="Admin Create"),
        MockPermission(id=2, action="admin.view", name="Admin View"),
        MockPermission(id=3, action="admin.delete", name="Admin Delete"),
    ]

    mock_service.set_users_permissions.return_value = mock_permissions

    response = await client.put(
        f"/api/admin/users/{target_user.id}/permissions",
        json=new_perms_ids,
        headers=admin_auth_headers,
    )

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 3
    assert {p["id"] for p in data} == set(new_perms_ids)

    # Verify service was called with correct args
    mock_service.set_users_permissions.assert_called_once()
    call_args = mock_service.set_users_permissions.call_args
    assert call_args[0][0] == target_user.id
    assert call_args[0][1] == new_perms_ids
    assert call_args[0][2].id == admin_user.id


async def test_put_permissions_forbidden(
    client: AsyncClient,
    mock_service: AsyncMock,
    override_permissions_service,
    admin_auth_headers,
    user_factory,
) -> None:
    target_user = await user_factory()
    new_perms_ids = [1, 2]

    response = await client.put(
        f"/api/admin/users/{target_user.id}/permissions",
        json=new_perms_ids,
        headers=admin_auth_headers,
    )

    assert response.status_code == 403
    mock_service.set_users_permissions.assert_not_called()


async def test_put_permissions_user_not_found(
    client: AsyncClient,
    mock_service: AsyncMock,
    override_permissions_service,
    mock_permissions_with_update,
    admin_auth_headers,
    admin_all_permissions,
) -> None:
    mock_service.set_users_permissions.side_effect = ValueError("User with provided ID not found")

    response = await client.put(
        "/api/admin/users/999999/permissions",
        json=[1],
        headers=admin_auth_headers,
    )

    assert response.status_code == 404
    assert response.json()["detail"] == ManagePermissionsResponses.USER_NOT_FOUND.detail  # type: ignore[attr-defined]
    mock_service.set_users_permissions.assert_called_once()
