from datetime import datetime, timedelta, timezone

import pytest
from httpx import AsyncClient

from app.domains.memberships.models import MembershipRequestStatusEnum
from app.domains.shared.transaction_managers import TransactionManager
from tests.fixtures.auth import AuthHeaders, UserFactory


pytestmark = pytest.mark.anyio


async def create_membership(
    transaction_manager: TransactionManager,
    *,
    user_id: int,
    membership_type_id: int,
    expires_at: datetime,
    request_fields: dict,
    **membership_fields,
) -> None:
    async with transaction_manager:
        membership_request = await transaction_manager.membership_requests_repository.create(
            user_id=user_id,
            membership_type_id=membership_type_id,
            status=MembershipRequestStatusEnum.APPROVED,
            **request_fields,
        )
        await transaction_manager.flush()
        await transaction_manager.user_membership_repository.create(
            user_id=user_id,
            membership_request_id=membership_request.id,
            membership_type_id=membership_type_id,
            expires_at=expires_at,
            **membership_fields,
        )


async def test_member_directory_requires_active_membership(
    client: AsyncClient,
    auth_headers: AuthHeaders,
) -> None:
    response = await client.get("/api/members", headers=auth_headers)

    assert response.status_code == 403
    assert response.json() == {"detail": "No active membership"}


async def test_member_directory_returns_only_active_members(
    client: AsyncClient,
    auth_headers: AuthHeaders,
    user_membership,
    user_factory: UserFactory,
    test_transaction_manager: TransactionManager,
    purchasable_membership_type_id: int,
    membership_request_fields: dict,
) -> None:
    active_member = await user_factory(pending=False, firstname="Alice", lastname="Directory")
    expired_member = await user_factory(pending=False, firstname="Expired", lastname="Directory")
    now = datetime.now(timezone.utc)
    await create_membership(
        test_transaction_manager,
        user_id=active_member.id,
        membership_type_id=purchasable_membership_type_id,
        expires_at=now + timedelta(days=30),
        request_fields=membership_request_fields,
    )
    await create_membership(
        test_transaction_manager,
        user_id=expired_member.id,
        membership_type_id=purchasable_membership_type_id,
        expires_at=now - timedelta(days=1),
        request_fields=membership_request_fields,
    )

    response = await client.get("/api/members?search=Directory", headers=auth_headers)

    assert response.status_code == 200
    payload = response.json()
    assert payload["count"] == 1
    assert [member["id"] for member in payload["data"]] == [active_member.id]
    assert payload["data"][0]["membership_type"]
    assert "email" not in payload["data"][0]
    assert "banned" not in payload["data"][0]


async def test_member_directory_supports_pagination(
    client: AsyncClient,
    auth_headers: AuthHeaders,
    user_membership,
    user_factory: UserFactory,
    test_transaction_manager: TransactionManager,
    purchasable_membership_type_id: int,
    membership_request_fields: dict,
) -> None:
    now = datetime.now(timezone.utc)
    for firstname in ("Anna", "Bella"):
        member = await user_factory(pending=False, firstname=firstname, lastname="Paging")
        await create_membership(
            test_transaction_manager,
            user_id=member.id,
            membership_type_id=purchasable_membership_type_id,
            expires_at=now + timedelta(days=30),
            request_fields=membership_request_fields,
        )

    response = await client.get(
        "/api/members?search=Paging&page=2&page_size=1&ordering=firstname",
        headers=auth_headers,
    )

    assert response.status_code == 200
    assert response.json()["count"] == 2
    assert response.json()["data"][0]["firstname"] == "Bella"
