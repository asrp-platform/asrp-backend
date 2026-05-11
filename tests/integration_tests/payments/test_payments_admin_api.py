import random

import pytest
from faker import Faker
from httpx import AsyncClient

from app.domains.payments.models import PaymentProvider, PaymentPurposeEnum, PaymentStatusEnum
from app.domains.users.models import User
from tests.fixtures.auth import AuthHeaders

pytestmark = pytest.mark.anyio


@pytest.fixture
def payment_factory(test_transaction_manager, test_user: User):
    """Factory to create test payments with random or specific data."""

    async def _create_payment(
        amount: int | None = None,
        status: PaymentStatusEnum | None = None,
        purpose: PaymentPurposeEnum | None = None,
        user_id: int | None = None,
    ):
        f = Faker()
        async with test_transaction_manager:
            return await test_transaction_manager.payment_repository.create(
                amount=amount or f.random_int(min=100, max=10000),
                status=status or random.choice(list(PaymentStatusEnum)),
                purpose=purpose or random.choice(list(PaymentPurposeEnum)),
                user_id=user_id or test_user.id,
                provider=PaymentProvider.STRIPE,
            )

    return _create_payment


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
    payment_factory,
) -> None:
    await payment_factory()

    response = await client.get("/api/admin/payments", headers=admin_auth_headers)

    assert response.status_code == 200
    data = response.json()
    assert data["count"] >= 1
    assert len(data["data"]) >= 1
