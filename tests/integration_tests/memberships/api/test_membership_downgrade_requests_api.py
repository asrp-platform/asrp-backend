import pytest
from httpx import AsyncClient

from app.domains.memberships.models import MembershipDowngradeRequest, UserMembership
from app.domains.shared.transaction_managers import TransactionManager
from tests.fixtures.auth import AuthHeaders


pytestmark = pytest.mark.anyio


async def get_updated_downgrade_request(
    transaction_manager: TransactionManager,
    downgrade_request_id: int,
) -> MembershipDowngradeRequest:
    async with transaction_manager:
        return await transaction_manager.membership_downgrade_requests_repository.get_first_by_kwargs(
            id=downgrade_request_id
        )


async def get_updated_request_and_membership(
    transaction_manager: TransactionManager,
    downgrade_request_id: int,
    user_membership_id: int,
) -> tuple[MembershipDowngradeRequest, UserMembership]:
    async with transaction_manager:
        updated_downgrade_request = (
            await transaction_manager.membership_downgrade_requests_repository.get_first_by_kwargs(
                id=downgrade_request_id
            )
        )
        updated_user_membership = await transaction_manager.user_membership_repository.get_first_by_kwargs(
            id=user_membership_id
        )

    return updated_downgrade_request, updated_user_membership


def assert_downgrade_response(
    data: dict,
    downgrade_request: MembershipDowngradeRequest,
    user_membership: UserMembership,
    *,
    approved: bool,
    admin_comment: str | None,
) -> None:
    assert data["id"] == downgrade_request.id
    assert data["target_membership_type_id"] == downgrade_request.target_membership_type_id
    assert data["user_membership_id"] == user_membership.id
    assert data["reason_changing"] == downgrade_request.reason_changing
    assert data["approved"] is approved
    assert data["admin_comment"] == admin_comment
    assert data["pending"] is False


def assert_updated_downgrade_request(
    downgrade_request: MembershipDowngradeRequest,
    *,
    approved: bool,
    admin_comment: str | None,
) -> None:
    assert downgrade_request.approved is approved
    assert downgrade_request.pending is False
    assert downgrade_request.admin_comment == admin_comment


# TODO: tests for membership downgrade request creation


async def test_approve_membership_downgrade_request(
    client: AsyncClient,
    test_transaction_manager: TransactionManager,
    admin_auth_headers: AuthHeaders,
    user_membership: UserMembership,
    membership_downgrade_request: MembershipDowngradeRequest,
    admin_all_permissions,
) -> None:
    response = await client.patch(
        f"/api/admin/memberships/types/downgrade-requests/{membership_downgrade_request.id}",
        headers=admin_auth_headers,
        json={"action": "approve"},
    )

    updated_downgrade_request, updated_user_membership = await get_updated_request_and_membership(
        test_transaction_manager,
        membership_downgrade_request.id,
        user_membership.id,
    )

    assert response.status_code == 200

    assert_downgrade_response(
        response.json(),
        membership_downgrade_request,
        user_membership,
        approved=True,
        admin_comment=None,
    )
    assert_updated_downgrade_request(
        updated_downgrade_request,
        approved=True,
        admin_comment=None,
    )

    assert updated_user_membership.membership_type_id == membership_downgrade_request.target_membership_type_id


async def test_reject_membership_downgrade_request(
    client: AsyncClient,
    test_transaction_manager: TransactionManager,
    user_membership: UserMembership,
    membership_downgrade_request: MembershipDowngradeRequest,
    admin_auth_headers: AuthHeaders,
    admin_all_permissions,
) -> None:
    admin_comment = "Current membership type is still required"

    response = await client.patch(
        f"/api/admin/memberships/types/downgrade-requests/{membership_downgrade_request.id}",
        headers=admin_auth_headers,
        json={"action": "reject", "admin_comment": admin_comment},
    )

    updated_downgrade_request, updated_user_membership = await get_updated_request_and_membership(
        test_transaction_manager,
        membership_downgrade_request.id,
        user_membership.id,
    )

    assert response.status_code == 200

    assert_downgrade_response(
        response.json(),
        membership_downgrade_request,
        user_membership,
        approved=False,
        admin_comment=admin_comment,
    )
    assert_updated_downgrade_request(
        updated_downgrade_request,
        approved=False,
        admin_comment=admin_comment,
    )

    assert updated_user_membership.membership_type_id == user_membership.membership_type_id


async def test_reject_membership_downgrade_request_without_admin_comment(
    client: AsyncClient,
    test_transaction_manager: TransactionManager,
    user_membership: UserMembership,
    membership_downgrade_request: MembershipDowngradeRequest,
    admin_auth_headers: AuthHeaders,
    admin_all_permissions,
) -> None:
    response = await client.patch(
        f"/api/admin/memberships/types/downgrade-requests/{membership_downgrade_request.id}",
        headers=admin_auth_headers,
        json={"action": "reject"},
    )

    updated_downgrade_request = await get_updated_downgrade_request(
        test_transaction_manager,
        membership_downgrade_request.id,
    )

    assert response.status_code == 422
    assert updated_downgrade_request.pending is True
    assert updated_downgrade_request.admin_comment is None
