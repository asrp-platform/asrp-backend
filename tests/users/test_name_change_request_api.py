from datetime import datetime, timezone

import pytest
from httpx import AsyncClient

from app.domains.users.infrastructure import UserTransactionManagerBase
from app.domains.users.models import NameChangeRequest, NameChangeRequestStatusEnum, User
from tests.fixtures.auth import AuthHeaders

pytestmark = pytest.mark.anyio


async def test_create_request_to_name_change(
    client: AsyncClient, test_user: User, auth_headers: AuthHeaders, name_change_request_data: dict
) -> None:
    response = await client.post(
        "api/users/current-user/name-change-requests",
        headers=auth_headers,
        json=name_change_request_data,
    )

    assert response.status_code == 201


async def test_get_all_requests_to_name_change(
    client: AsyncClient, admin_auth_headers: AuthHeaders, admin_all_permissions
) -> None:
    response = await client.get(
        "api/admin/users/name-change-requests",
        headers=admin_auth_headers,
    )

    assert response.status_code == 200


async def test_get_request_to_name_change(
    client: AsyncClient, name_change_request: NameChangeRequest, admin_auth_headers: AuthHeaders, admin_all_permissions
) -> None:
    response = await client.get(
        f"api/admin/users/{name_change_request.user_id}/name-change-requests/{name_change_request.id}",
        headers=admin_auth_headers,
    )

    assert response.status_code == 200


async def test_approve_request_to_name_change(
    client: AsyncClient,
    name_change_request: NameChangeRequest,
    admin_auth_headers: AuthHeaders,
    admin_all_permissions,
    name_change_request_approve_data: dict,
) -> None:
    response = await client.patch(
        f"api/admin/users/{name_change_request.user_id}/name-change-requests/{name_change_request.id}",
        headers=admin_auth_headers,
        json=name_change_request_approve_data,
    )

    assert response.status_code == 204


async def test_reject_request_to_name_change(
    client: AsyncClient,
    name_change_request: NameChangeRequest,
    admin_auth_headers: AuthHeaders,
    admin_all_permissions,
    name_change_request_reject_data: dict,
) -> None:
    response = await client.patch(
        f"api/admin/users/{name_change_request.user_id}/name-change-requests/{name_change_request.id}",
        headers=admin_auth_headers,
        json=name_change_request_reject_data,
    )

    assert response.status_code == 204


async def test_create_request_to_name_change_not_authorized(
    client: AsyncClient, test_user: User, name_change_request_data: dict
) -> None:
    response = await client.post("api/users/current-user/name-change-requests", json=name_change_request_data)

    assert response.status_code == 401


async def test_get_all_requests_to_name_change_not_authorized(
    client: AsyncClient,
) -> None:
    response = await client.get("api/admin/users/name-change-requests")

    assert response.status_code == 401


async def test_get_request_to_name_change_not_authorized(
    client: AsyncClient,
    name_change_request: NameChangeRequest,
) -> None:
    response = await client.get(
        f"api/admin/users/{name_change_request.user_id}/name-change-requests/{name_change_request.id}"
    )

    assert response.status_code == 401


async def test_update_request_to_name_change_not_authorized(
    client: AsyncClient, name_change_request: NameChangeRequest, name_change_request_approve_data: dict
) -> None:
    response = await client.patch(
        f"api/admin/users/{name_change_request.user_id}/name-change-requests/{name_change_request.id}",
        json=name_change_request_approve_data,
    )

    assert response.status_code == 401


async def test_get_request_to_name_change_does_not_exist(
    client: AsyncClient, test_user: User, admin_auth_headers: AuthHeaders, admin_all_permissions
) -> None:
    response = await client.get(
        f"api/admin/users/{test_user.id}/name-change-requests/99999999", headers=admin_auth_headers
    )

    assert response.status_code == 404


async def test_update_request_to_name_change_does_not_exist(
    client: AsyncClient,
    test_user: User,
    admin_auth_headers: AuthHeaders,
    admin_all_permissions,
    name_change_request_approve_data: dict,
) -> None:
    response = await client.patch(
        f"api/admin/users/{test_user.id}/name-change-requests/99999999",
        headers=admin_auth_headers,
        json=name_change_request_approve_data,
    )

    assert response.status_code == 404


async def test_create_name_change_request_when_active_request_already_exists(
    client: AsyncClient,
    name_change_request: NameChangeRequest,
    auth_headers: AuthHeaders,
    name_change_request_data: dict,
) -> None:
    response = await client.post(
        "api/users/current-user/name-change-requests",
        headers=auth_headers,
        json=name_change_request_data,
    )

    assert response.status_code == 409


async def test_create_name_change_request_when_cooldown_not_expired(
    client: AsyncClient,
    user_uow: UserTransactionManagerBase,
    name_change_request: NameChangeRequest,
    auth_headers: AuthHeaders,
    name_change_request_data: dict,
) -> None:
    async with user_uow:
        await user_uow.user_repository.update(
            name_change_request.user_id,
            last_name_change=datetime.now(tz=timezone.utc),
        )

        await user_uow.name_change_request_repository.update(
            name_change_request.id,
            status=NameChangeRequestStatusEnum.APPROVED,
        )

    response = await client.post(
        "api/users/current-user/name-change-requests",
        headers=auth_headers,
        json=name_change_request_data,
    )

    assert response.status_code == 429


async def test_update_request_to_name_change_invalid_action(
    client: AsyncClient,
    name_change_request: NameChangeRequest,
    admin_auth_headers: AuthHeaders,
    admin_all_permissions,
    name_change_request_approve_data: dict,
) -> None:
    name_change_request_approve_data["action"] = "invalid_action"

    response = await client.patch(
        f"api/admin/users/{name_change_request.user_id}/name-change-requests/{name_change_request.id}",
        headers=admin_auth_headers,
        json=name_change_request_approve_data,
    )

    assert response.status_code == 422


async def test_reject_request_to_name_change_without_reason(
    client: AsyncClient,
    name_change_request: NameChangeRequest,
    admin_auth_headers: AuthHeaders,
    admin_all_permissions,
    name_change_request_reject_data: dict,
) -> None:
    name_change_request_reject_data["reason_rejecting"] = None

    response = await client.patch(
        f"api/admin/users/{name_change_request.user_id}/name-change-requests/{name_change_request.id}",
        headers=admin_auth_headers,
        json=name_change_request_reject_data,
    )

    assert response.status_code == 422
