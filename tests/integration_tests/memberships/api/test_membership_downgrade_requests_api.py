from datetime import datetime, timedelta, timezone

import pytest
from httpx import AsyncClient

from app.domains.memberships.models import MembershipDowngradeRequest, MembershipRequest, UserMembership
from app.domains.shared.transaction_managers import TransactionManager
from tests.fixtures.auth import AuthHeaders

pytestmark = pytest.mark.anyio


REVIEW_RESPONSE_FIELDS = {
    "id",
    "created_at",
    "updated_at",
    "target_membership_type_id",
    "user_membership_id",
    "reason_changing",
    "approved",
    "admin_comment",
    "pending",
}


async def _create_membership_downgrade_request(
    test_transaction_manager: TransactionManager,
    membership_request: MembershipRequest,
) -> tuple[UserMembership, MembershipDowngradeRequest]:
    async with test_transaction_manager:
        membership_types, _ = await test_transaction_manager.membership_type_repository.list()
        target_membership_type = next(
            membership_type
            for membership_type in membership_types
            if membership_type.id != membership_request.membership_type_id
        )

        user_membership = await test_transaction_manager.user_membership_repository.create(
            user_id=membership_request.user_id,
            membership_request_id=membership_request.id,
            membership_type_id=membership_request.membership_type_id,
            expires_at=datetime.now(timezone.utc) + timedelta(days=30),
        )
        await test_transaction_manager.flush()

        downgrade_request = await test_transaction_manager.membership_downgrade_requests_repository.create(
            user_membership_id=user_membership.id,
            target_membership_type_id=target_membership_type.id,
            reason_changing="I want to switch to a cheaper membership type",
        )

    return user_membership, downgrade_request


async def test_approve_membership_downgrade_request(
    client: AsyncClient,
    test_transaction_manager: TransactionManager,
    paid_membership_request: MembershipRequest,
    admin_auth_headers: AuthHeaders,
    admin_all_permissions,
) -> None:
    user_membership, downgrade_request = await _create_membership_downgrade_request(
        test_transaction_manager,
        paid_membership_request,
    )

    response = await client.patch(
        f"/api/admin/memberships/types/downgrade-requests/{downgrade_request.id}",
        headers=admin_auth_headers,
        json={"action": "approve"},
    )

    async with test_transaction_manager:
        updated_downgrade_request = (
            await test_transaction_manager.membership_downgrade_requests_repository.get_first_by_kwargs(
                id=downgrade_request.id
            )
        )
        updated_user_membership = await test_transaction_manager.user_membership_repository.get_first_by_kwargs(
            id=user_membership.id
        )

    assert response.status_code == 200
    data = response.json()
    assert set(data) == REVIEW_RESPONSE_FIELDS
    assert data["id"] == downgrade_request.id
    assert data["target_membership_type_id"] == downgrade_request.target_membership_type_id
    assert data["user_membership_id"] == user_membership.id
    assert data["reason_changing"] == downgrade_request.reason_changing
    assert data["approved"] is True
    assert data["admin_comment"] is None
    assert data["pending"] is False
    assert updated_downgrade_request.approved is True
    assert updated_downgrade_request.pending is False
    assert updated_downgrade_request.admin_comment is None
    assert updated_user_membership.membership_type_id == downgrade_request.target_membership_type_id


async def test_reject_membership_downgrade_request(
    client: AsyncClient,
    test_transaction_manager: TransactionManager,
    paid_membership_request: MembershipRequest,
    admin_auth_headers: AuthHeaders,
    admin_all_permissions,
) -> None:
    user_membership, downgrade_request = await _create_membership_downgrade_request(
        test_transaction_manager,
        paid_membership_request,
    )
    admin_comment = "Current membership type is still required"

    response = await client.patch(
        f"/api/admin/memberships/types/downgrade-requests/{downgrade_request.id}",
        headers=admin_auth_headers,
        json={"action": "reject", "admin_comment": admin_comment},
    )

    async with test_transaction_manager:
        updated_downgrade_request = (
            await test_transaction_manager.membership_downgrade_requests_repository.get_first_by_kwargs(
                id=downgrade_request.id
            )
        )
        updated_user_membership = await test_transaction_manager.user_membership_repository.get_first_by_kwargs(
            id=user_membership.id
        )

    assert response.status_code == 200
    data = response.json()
    assert set(data) == REVIEW_RESPONSE_FIELDS
    assert data["id"] == downgrade_request.id
    assert data["target_membership_type_id"] == downgrade_request.target_membership_type_id
    assert data["user_membership_id"] == user_membership.id
    assert data["reason_changing"] == downgrade_request.reason_changing
    assert data["approved"] is False
    assert data["admin_comment"] == admin_comment
    assert data["pending"] is False
    assert updated_downgrade_request.approved is False
    assert updated_downgrade_request.pending is False
    assert updated_downgrade_request.admin_comment == admin_comment
    assert updated_user_membership.membership_type_id == user_membership.membership_type_id


async def test_reject_membership_downgrade_request_without_admin_comment(
    client: AsyncClient,
    test_transaction_manager: TransactionManager,
    paid_membership_request: MembershipRequest,
    admin_auth_headers: AuthHeaders,
    admin_all_permissions,
) -> None:
    _, downgrade_request = await _create_membership_downgrade_request(
        test_transaction_manager,
        paid_membership_request,
    )

    response = await client.patch(
        f"/api/admin/memberships/types/downgrade-requests/{downgrade_request.id}",
        headers=admin_auth_headers,
        json={"action": "reject"},
    )

    async with test_transaction_manager:
        updated_downgrade_request = (
            await test_transaction_manager.membership_downgrade_requests_repository.get_first_by_kwargs(
                id=downgrade_request.id
            )
        )

    assert response.status_code == 422
    assert updated_downgrade_request.pending is True
    assert updated_downgrade_request.admin_comment is None
