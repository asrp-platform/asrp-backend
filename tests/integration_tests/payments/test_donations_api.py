from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from faker import Faker
from httpx import AsyncClient

from app.domains.payments.models import PaymentPurposeEnum, PaymentStatusEnum
from app.domains.shared.transaction_managers import TransactionManager


pytestmark = pytest.mark.anyio


async def test_make_donation(
    client: AsyncClient,
    faker: Faker,
    test_transaction_manager: TransactionManager,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    checkout_session = SimpleNamespace(
        id=f"cs_test_{faker.uuid4()}",
        status="open",
        payment_status="unpaid",
        url="https://checkout.stripe.com/test/donation",
    )
    create_checkout_session = AsyncMock(return_value=checkout_session)
    monkeypatch.setattr(
        "app.domains.payments.use_cases.make_donation.create_checkout_session",
        create_checkout_session,
    )

    response = await client.post(
        "/api/payments/donations",
        json={
            "amount_usd": faker.pyint(min_value=5),
            "customer_email": faker.email(),
        },
    )

    payment_id = create_checkout_session.await_args.kwargs["metadata"]["payment_id"]
    async with test_transaction_manager:
        payment = await test_transaction_manager.payment_repository.get_first_by_kwargs(id=payment_id)

    assert response.status_code == 201
    assert response.json()["checkout_session_url"] == checkout_session.url
    assert payment is not None
    assert payment.status == PaymentStatusEnum.PENDING
    assert payment.purpose == PaymentPurposeEnum.DONATION
