from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from app.domains.payments.models import PaymentPurposeEnum
from app.domains.payments.stripe import utils as stripe_utils


pytestmark = pytest.mark.anyio


async def test_create_checkout_session_prefills_customer_email(monkeypatch: pytest.MonkeyPatch) -> None:
    created_session = SimpleNamespace(id="cs_test")
    created_kwargs = {}

    def create_session(**kwargs):
        created_kwargs.update(kwargs)
        return created_session

    monkeypatch.setattr(stripe_utils.stripe.checkout.Session, "create", create_session)

    result = await stripe_utils.create_checkout_session(
        [{"price": "price_test", "quantity": 1}],
        metadata={"payment_purpose": PaymentPurposeEnum.MEMBERSHIP_RENEWAL.value},
        success_url="https://example.com/success",
        customer_email="member@example.com",
    )

    assert result == created_session
    assert created_kwargs["customer_email"] == "member@example.com"


async def test_membership_renewal_checkout_session_passes_user_email(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    checkout_session = SimpleNamespace(
        id="cs_renewal",
        status="open",
        payment_status="unpaid",
        url="https://checkout.stripe.com/renewal",
    )
    create_checkout_session = AsyncMock(return_value=checkout_session)
    monkeypatch.setattr(stripe_utils, "create_checkout_session", create_checkout_session)

    payment = SimpleNamespace(id=123)
    membership_type = SimpleNamespace(
        name="Active Membership",
        description="Annual active membership",
        price_usd=Decimal("120.00"),
    )
    user_membership = SimpleNamespace(id=456)

    result = await stripe_utils.create_membership_renewal_checkout_session(
        payment=payment,
        membership_type=membership_type,
        user_membership=user_membership,
        user_email="member@example.com",
    )

    assert result.session == checkout_session
    create_checkout_session.assert_awaited_once()
    assert create_checkout_session.await_args.kwargs["customer_email"] == "member@example.com"
