from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, patch

import pytest
from httpx import AsyncClient

from app.domains.emails.email_queue import EmailQueue
from app.domains.memberships.models import MembershipDowngradeRequest, MembershipRequest, UserMembership
from app.domains.shared.transaction_managers import TransactionManager
from tests.fixtures.auth import AuthHeaders


pytestmark = pytest.mark.anyio


@pytest.fixture()
async def active_user_membership(
    test_transaction_manager: TransactionManager,
    paid_membership_request: MembershipRequest,
) -> UserMembership:
    async with test_transaction_manager:
        user_membership = await test_transaction_manager.user_membership_repository.create(
            user_id=paid_membership_request.user_id,
            membership_request_id=paid_membership_request.id,
            membership_type_id=paid_membership_request.membership_type_id,
            expires_at=datetime.now(timezone.utc) + timedelta(days=30),
        )
        await test_transaction_manager.flush()
        return user_membership


@pytest.fixture()
async def suspended_user_membership(
    test_transaction_manager: TransactionManager,
    active_user_membership: UserMembership,
) -> UserMembership:
    async with test_transaction_manager:
        return await test_transaction_manager.user_membership_repository.update(
            active_user_membership.id,
            suspended_until=datetime.now(timezone.utc) + timedelta(days=7),
            suspension_reason="Terms violation",
            suspended_at=datetime.now(timezone.utc),
        )


@pytest.fixture()
async def terminated_user_membership(
    test_transaction_manager: TransactionManager,
    active_user_membership: UserMembership,
) -> UserMembership:
    async with test_transaction_manager:
        return await test_transaction_manager.user_membership_repository.update(
            active_user_membership.id,
            terminated=True,
            termination_reason="Repeated terms violation",
            terminated_at=datetime.now(timezone.utc),
        )


@pytest.fixture()
async def membership_downgrade_request(
    test_transaction_manager: TransactionManager,
    active_user_membership: UserMembership,
):
    async with test_transaction_manager:
        membership_types, _ = await test_transaction_manager.membership_type_repository.list()
        target_membership_type = next(
            membership_type
            for membership_type in membership_types
            if membership_type.id != active_user_membership.membership_type_id
        )
        return await test_transaction_manager.membership_downgrade_requests_repository.create(
            user_membership_id=active_user_membership.id,
            target_membership_type_id=target_membership_type.id,
            reason_changing="I want to switch to a cheaper membership type",
        )


async def test_get_all_members(
    client: AsyncClient,
    active_user_membership: UserMembership,
    admin_auth_headers: AuthHeaders,
    admin_all_permissions,
) -> None:
    response = await client.get("/api/admin/memberships/members", headers=admin_auth_headers)

    assert response.status_code == 200


async def test_suspend_membership(
    client: AsyncClient,
    active_user_membership: UserMembership,
    admin_auth_headers: AuthHeaders,
    admin_all_permissions,
) -> None:
    with patch.object(EmailQueue, "send_email", new_callable=AsyncMock) as mock_send_email:
        response = await client.post(
            f"/api/admin/memberships/{active_user_membership.id}/restrictions",
            headers=admin_auth_headers,
            json={
                "suspended_until": (datetime.now(timezone.utc) + timedelta(days=7)).isoformat(),
                "reason": "Terms violation",
            },
        )

    assert response.status_code == 201
    mock_send_email.assert_awaited_once()


async def test_terminate_membership(
    client: AsyncClient,
    active_user_membership: UserMembership,
    admin_auth_headers: AuthHeaders,
    admin_all_permissions,
) -> None:
    with patch.object(EmailQueue, "send_email", new_callable=AsyncMock) as mock_send_email:
        response = await client.post(
            f"/api/admin/memberships/{active_user_membership.id}/restrictions",
            headers=admin_auth_headers,
            json={
                "suspended_until": None,
                "reason": "Repeated terms violation",
            },
        )

    assert response.status_code == 201
    mock_send_email.assert_awaited_once()


async def test_restrict_membership_not_found(
    client: AsyncClient,
    admin_auth_headers: AuthHeaders,
    admin_all_permissions,
) -> None:
    response = await client.post(
        "/api/admin/memberships/999999/restrictions",
        headers=admin_auth_headers,
        json={
            "suspended_until": (datetime.now(timezone.utc) + timedelta(days=7)).isoformat(),
            "reason": "Terms violation",
        },
    )

    assert response.status_code == 404


async def test_restrict_membership_with_past_suspended_until(
    client: AsyncClient,
    active_user_membership: UserMembership,
    admin_auth_headers: AuthHeaders,
    admin_all_permissions,
) -> None:
    response = await client.post(
        f"/api/admin/memberships/{active_user_membership.id}/restrictions",
        headers=admin_auth_headers,
        json={
            "suspended_until": (datetime.now(timezone.utc) - timedelta(days=1)).isoformat(),
            "reason": "Terms violation",
        },
    )

    assert response.status_code == 422


async def test_restrict_suspended_membership(
    client: AsyncClient,
    suspended_user_membership: UserMembership,
    admin_auth_headers: AuthHeaders,
    admin_all_permissions,
) -> None:
    response = await client.post(
        f"/api/admin/memberships/{suspended_user_membership.id}/restrictions",
        headers=admin_auth_headers,
        json={
            "suspended_until": (datetime.now(timezone.utc) + timedelta(days=14)).isoformat(),
            "reason": "Terms violation",
        },
    )

    assert response.status_code == 409


async def test_restrict_terminated_membership(
    client: AsyncClient,
    terminated_user_membership: UserMembership,
    admin_auth_headers: AuthHeaders,
    admin_all_permissions,
) -> None:
    response = await client.post(
        f"/api/admin/memberships/{terminated_user_membership.id}/restrictions",
        headers=admin_auth_headers,
        json={
            "suspended_until": (datetime.now(timezone.utc) + timedelta(days=14)).isoformat(),
            "reason": "Terms violation",
        },
    )

    assert response.status_code == 409


async def test_get_membership_downgrade_requests(
    client: AsyncClient,
    membership_downgrade_request,
    admin_auth_headers: AuthHeaders,
    admin_all_permissions,
) -> None:
    response = await client.get(
        "/api/admin/memberships/types/downgrade-requests",
        headers=admin_auth_headers,
    )

    assert response.status_code == 200


async def test_approve_membership_downgrade_request(
    client: AsyncClient,
    membership_downgrade_request: MembershipDowngradeRequest,
    admin_auth_headers: AuthHeaders,
    admin_all_permissions,
) -> None:
    response = await client.patch(
        f"/api/admin/memberships/types/downgrade-requests/{membership_downgrade_request.id}",
        headers=admin_auth_headers,
        json={"action": "approve"},
    )

    assert response.status_code == 200


async def test_reject_membership_downgrade_request(
    client: AsyncClient,
    membership_downgrade_request: MembershipDowngradeRequest,
    admin_auth_headers: AuthHeaders,
    admin_all_permissions,
) -> None:
    response = await client.patch(
        f"/api/admin/memberships/types/downgrade-requests/{membership_downgrade_request.id}",
        headers=admin_auth_headers,
        json={"action": "reject", "admin_comment": "Current membership type is still required"},
    )

    assert response.status_code == 200


async def test_reject_membership_downgrade_request_without_admin_comment(
    client: AsyncClient,
    membership_downgrade_request: MembershipDowngradeRequest,
    admin_auth_headers: AuthHeaders,
    admin_all_permissions,
) -> None:
    response = await client.patch(
        f"/api/admin/memberships/types/downgrade-requests/{membership_downgrade_request.id}",
        headers=admin_auth_headers,
        json={"action": "reject"},
    )

    assert response.status_code == 422
