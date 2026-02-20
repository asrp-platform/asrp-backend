import pytest
from datetime import datetime, timezone
from httpx import AsyncClient

from app.domains.users.infrastructure import UserUnitOfWork
from app.domains.users.models import User, UsernameChange, UsernameChangeStatusEnum
from tests.fixtures.auth import AuthHeaders

pytestmark = pytest.mark.anyio


async def test_create_request_to_username_change(
    client: AsyncClient,
    test_user: User,
    auth_headers: AuthHeaders,
    username_change_data: dict
) -> None:
    response = await client.post(
        f"api/users/{test_user.id}/username-changes",
        headers=auth_headers,
        json=username_change_data,
    )

    assert response.status_code == 201


async def test_get_all_requests_to_username_change(
    client: AsyncClient,
    admin_auth_headers: AuthHeaders,
    admin_all_permissions
) -> None:
    response = await client.get(
        "api/admin/users/username-changes",
        headers=admin_auth_headers,
    )

    assert response.status_code == 200


async def test_get_request_to_username_change(
    client: AsyncClient,
    username_change: UsernameChange,
    admin_auth_headers: AuthHeaders,
    admin_all_permissions
) -> None:
    response = await client.get(
        f"api/admin/users/{username_change.user_id}/username-changes/{username_change.id}",
        headers=admin_auth_headers,
    )

    assert response.status_code == 200


async def test_approve_request_to_username_change(
    client: AsyncClient,
    username_change: UsernameChange,
    admin_auth_headers: AuthHeaders,
    admin_all_permissions
) -> None:
    response = await client.patch(
        f"api/admin/users/{username_change.user_id}/username-changes/{username_change.id}/approve",
        headers=admin_auth_headers,
    )

    assert response.status_code == 200


async def test_reject_request_to_username_change(
    client: AsyncClient,
    username_change: UsernameChange,
    admin_auth_headers: AuthHeaders,
    admin_all_permissions,
    username_reject_change_data: dict
) -> None:
    response = await client.patch(
        f"api/admin/users/{username_change.user_id}/username-changes/{username_change.id}/reject",
        headers=admin_auth_headers,
        json=username_reject_change_data
    )

    assert response.status_code == 200


async def test_create_request_to_username_change_not_authorized(
    client: AsyncClient,
    test_user: User,
    username_change_data: dict
) -> None:
    response = await client.post(
        f"api/users/{test_user.id}/username-changes",
        json=username_change_data
    )

    assert response.status_code == 401


async def test_get_all_requests_to_username_change_not_authorized(
    client: AsyncClient,
) -> None:
    response = await client.get("api/admin/users/username-changes")

    assert response.status_code == 401


async def test_get_request_to_username_change_not_authorized(
    client: AsyncClient,
    username_change: UsernameChange,
) -> None:
    response = await client.get(
        f"api/admin/users/{username_change.user_id}/username-changes/{username_change.id}"
    )

    assert response.status_code == 401


async def test_approve_request_to_username_change_not_authorized(
    client: AsyncClient,
    username_change: UsernameChange,
) -> None:
    response = await client.patch(
        f"api/admin/users/{username_change.user_id}/username-changes/{username_change.id}/approve"
    )

    assert response.status_code == 401



async def test_reject_request_to_username_change_not_authorized(
    client: AsyncClient,
    username_change: UsernameChange,
) -> None:
    response = await client.patch(
        f"api/admin/users/{username_change.user_id}/username-changes/{username_change.id}/reject"
    )

    assert response.status_code == 401

async def test_get_request_to_username_change_does_not_exist(
    client: AsyncClient,
    test_user: User,
    admin_auth_headers: AuthHeaders,
    admin_all_permissions
) -> None:
    response = await client.get(
        f"api/admin/users/{test_user.id}/username-changes/99999999",
        headers=admin_auth_headers
    )

    assert response.status_code == 404


async def test_approve_request_to_username_change_does_not_exist(
    client: AsyncClient,
    test_user: User,
    admin_auth_headers: AuthHeaders,
    admin_all_permissions
) -> None:
    response = await client.patch(
        f"api/admin/users/{test_user.id}/username-changes/99999999/approve",
        headers=admin_auth_headers
    )

    assert response.status_code == 404


async def test_reject_request_to_username_change_does_not_exist(
    client: AsyncClient,
    test_user: User,
    admin_auth_headers: AuthHeaders,
    admin_all_permissions,
    username_reject_change_data: dict
) -> None:
    response = await client.patch(
        f"api/admin/users/{test_user.id}/username-changes/99999999/reject",
        headers=admin_auth_headers,
        json=username_reject_change_data
    )

    assert response.status_code == 404


async def test_create_username_change_request_when_active_request_already_exists(
    client: AsyncClient,
    username_change: UsernameChange,
    auth_headers: AuthHeaders,
    username_change_data: dict
) -> None:
    response = await client.post(
        f"api/users/{username_change.user_id}/username-changes",
        headers=auth_headers,
        json=username_change_data,
    )

    assert response.status_code == 409


async def test_create_username_change_request_when_cooldown_not_expired(
    client: AsyncClient,
    user_uow: UserUnitOfWork,
    username_change: UsernameChange,
    auth_headers: AuthHeaders,
    username_change_data: dict
) -> None:
    async with user_uow:
        await user_uow.user_repository.update(
            username_change.user_id,
            {"last_name_change": datetime.now(tz=timezone.utc)}
        )

        await user_uow.username_change_repository.update(
            username_change.id,
            {"status": UsernameChangeStatusEnum.APPROVED}
        )

    response = await client.post(
        f"api/users/{username_change.user_id}/username-changes",
        headers=auth_headers,
        json=username_change_data,
    )

    assert response.status_code == 429
