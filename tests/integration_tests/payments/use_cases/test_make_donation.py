from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

import app.domains.payments.use_cases.make_donation as make_donation_module
from app.domains.payments.models import PaymentProvider, PaymentPurposeEnum, PaymentStatusEnum
from app.domains.payments.services import PaymentService
from app.domains.payments.use_cases.make_donation import MakeDonationUseCase
from app.domains.shared.transaction_managers import TransactionManager


pytestmark = pytest.mark.anyio


@pytest.fixture()
def make_donation_use_case(
    test_transaction_manager: TransactionManager,
    payment_service: PaymentService,
) -> MakeDonationUseCase:
    return MakeDonationUseCase(test_transaction_manager, payment_service)


async def test_make_donation_creates_pending_donation_payment(
    make_donation_use_case: MakeDonationUseCase,
    test_transaction_manager: TransactionManager,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    checkout_session = SimpleNamespace(
        id="cs_donation_success",
        status="open",
        payment_status="unpaid",
        url="https://checkout.stripe.com/donation-success",
    )
    create_checkout_session = AsyncMock(return_value=checkout_session)
    monkeypatch.setattr(make_donation_module, "create_checkout_session", create_checkout_session)

    result = await make_donation_use_case.execute(
        price_usd=Decimal("10.125"),
        customer_email="donor@example.com",
    )

    checkout_kwargs = create_checkout_session.await_args.kwargs
    payment_id = checkout_kwargs["metadata"]["payment_id"]
    async with test_transaction_manager:
        payment = await test_transaction_manager.payment_repository.get_first_by_kwargs(id=payment_id)

    assert result == checkout_session.url
    assert payment is not None
    assert payment.provider == PaymentProvider.STRIPE
    assert payment.amount == Decimal("1013")
    assert payment.status == PaymentStatusEnum.PENDING
    assert payment.purpose == PaymentPurposeEnum.DONATION
    assert payment.user_id is None
    assert payment.provider_data == {
        "payment_id": str(payment.id),
        "checkout_session_id": checkout_session.id,
        "checkout_session_status": checkout_session.status,
        "payment_intent_status": checkout_session.payment_status,
        "url": checkout_session.url,
    }

    create_checkout_session.assert_awaited_once()
    assert checkout_kwargs["metadata"] == {
        "payment_id": payment.id,
        "payment_purpose": PaymentPurposeEnum.DONATION.value,
    }
    assert checkout_kwargs["line_items"] == make_donation_use_case._build_donation_line_items(1013)
    assert checkout_kwargs["customer_email"] == "donor@example.com"
    assert checkout_kwargs["mode"] == "payment"
    assert checkout_kwargs["submit_type"] == "donate"


async def test_make_donation_marks_exact_payment_failed_when_checkout_creation_fails(
    make_donation_use_case: MakeDonationUseCase,
    test_transaction_manager: TransactionManager,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    create_checkout_session = AsyncMock(side_effect=RuntimeError("stripe is down"))
    monkeypatch.setattr(make_donation_module, "create_checkout_session", create_checkout_session)

    with pytest.raises(RuntimeError, match="stripe is down"):
        await make_donation_use_case.execute(
            price_usd=Decimal("25.00"),
            customer_email="donor@example.com",
        )

    payment_id = create_checkout_session.await_args.kwargs["metadata"]["payment_id"]
    async with test_transaction_manager:
        payment = await test_transaction_manager.payment_repository.get_first_by_kwargs(id=payment_id)

    assert payment is not None
    assert payment.status == PaymentStatusEnum.FAILED
    assert payment.purpose == PaymentPurposeEnum.DONATION
    assert payment.provider_data == {
        "payment_id": str(payment.id),
        "error_type": "checkout_session_error",
    }
    create_checkout_session.assert_awaited_once()
