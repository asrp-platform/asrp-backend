import pytest
from httpx import AsyncClient

from app.domains.payments.models import PaymentProvider, PaymentPurposeEnum, PaymentStatusEnum
from app.domains.users.models import User
from tests.fixtures.auth import AuthHeaders

pytestmark = pytest.mark.anyio


async def test_get_payments_admin_not_authenticated(client: AsyncClient) -> None:
    response = await client.get("/api/admin/payments")
    assert response.status_code == 401


async def test_get_payments_admin_unauthorized(client: AsyncClient, auth_headers: AuthHeaders) -> None:
    response = await client.get("/api/admin/payments", headers=auth_headers)
    assert response.status_code == 403


async def test_get_payments_admin_success(
    client: AsyncClient,
    admin_auth_headers: AuthHeaders,
    admin_all_permissions,
    test_transaction_manager,
    test_user: User,
) -> None:
    # Create some payments
    async with test_transaction_manager:
        await test_transaction_manager.payment_repository.create(
            amount=100,
            status=PaymentStatusEnum.SUCCEEDED,
            purpose=PaymentPurposeEnum.MEMBERSHIP_APPLICATION,
            user_id=test_user.id,
            provider=PaymentProvider.STRIPE,
        )

    response = await client.get("/api/admin/payments", headers=admin_auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["count"] >= 1
    assert len(data["data"]) >= 1


async def test_get_payments_admin_filters(
    client: AsyncClient,
    admin_auth_headers: AuthHeaders,
    admin_all_permissions,
    test_transaction_manager,
    test_user: User,
) -> None:
    async with test_transaction_manager:
        # Payment 1
        await test_transaction_manager.payment_repository.create(
            amount=100,
            status=PaymentStatusEnum.SUCCEEDED,
            purpose=PaymentPurposeEnum.MEMBERSHIP_APPLICATION,
            user_id=test_user.id,
            provider=PaymentProvider.STRIPE,
        )
        # Payment 2
        await test_transaction_manager.payment_repository.create(
            amount=200,
            status=PaymentStatusEnum.PENDING,
            purpose=PaymentPurposeEnum.DONATION,
            user_id=test_user.id,
            provider=PaymentProvider.STRIPE,
        )

    # Filter by purpose
    response = await client.get(
        "/api/admin/payments", headers=admin_auth_headers, params={"purpose": PaymentPurposeEnum.DONATION.value}
    )
    assert response.status_code == 200, response.json()
    data = response.json()
    assert all(p["purpose"] == PaymentPurposeEnum.DONATION.value for p in data["data"])

    # Filter by user_id
    response = await client.get("/api/admin/payments", headers=admin_auth_headers, params={"user_id": test_user.id})
    assert response.status_code == 200
    data = response.json()
    assert all(p["user_id"] == test_user.id for p in data["data"])


async def test_get_payments_admin_pagination(
    client: AsyncClient,
    admin_auth_headers: AuthHeaders,
    admin_all_permissions,
    test_transaction_manager,
    test_user: User,
) -> None:
    async with test_transaction_manager:
        for i in range(5):
            await test_transaction_manager.payment_repository.create(
                amount=100 + i,
                status=PaymentStatusEnum.SUCCEEDED,
                purpose=PaymentPurposeEnum.MEMBERSHIP_APPLICATION,
                user_id=test_user.id,
                provider=PaymentProvider.STRIPE,
            )

    response = await client.get("/api/admin/payments", headers=admin_auth_headers, params={"page_size": 2, "page": 1})
    assert response.status_code == 200
    data = response.json()
    assert len(data["data"]) == 2
    assert data["count"] >= 5
