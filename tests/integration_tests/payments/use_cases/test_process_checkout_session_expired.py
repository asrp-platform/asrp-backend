from types import SimpleNamespace

import pytest
from faker import Faker

from app.domains.payments.models import Payment, PaymentStatusEnum
from app.domains.payments.use_cases.process_checkout_session_expired import ProcessCheckoutSessionExpiredUseCase
from app.domains.shared.transaction_managers import TransactionManager

pytestmark = pytest.mark.anyio


@pytest.fixture()
def process_checkout_session_expired_use_case(
    test_transaction_manager: TransactionManager,
    payment_service,
):
    return ProcessCheckoutSessionExpiredUseCase(
        transaction_manager=test_transaction_manager,
        payment_service=payment_service,
    )


@pytest.fixture()
def expired_checkout_session_event(faker: Faker, pending_payment: Payment):
    checkout_session = SimpleNamespace(
        id=f"cs_expired_{faker.uuid4()}",
        status="expired",
        payment_status="unpaid",
        metadata=SimpleNamespace(
            payment_id=str(pending_payment.id),
            membership_request_id=str(pending_payment.provider_data["membership_request_id"]),
        ),
    )

    return SimpleNamespace(
        id=f"evt_{faker.uuid4()}",
        type="checkout.session.expired",
        data=SimpleNamespace(object=checkout_session),
    )


async def test_process_checkout_session_expired_marks_pending_payment_as_expired(
    process_checkout_session_expired_use_case: ProcessCheckoutSessionExpiredUseCase,
    expired_checkout_session_event,
    payment_service,
    pending_payment: Payment,
):
    await process_checkout_session_expired_use_case.execute(expired_checkout_session_event)

    checkout_session = expired_checkout_session_event.data.object
    updated_payment = await payment_service.get_payment_by_id(str(pending_payment.id))
    processed_event = await payment_service.get_processed_webhook_event_by_kwargs(
        event_id=expired_checkout_session_event.id,
    )

    assert updated_payment.status == PaymentStatusEnum.EXPIRED
    assert updated_payment.provider_data["checkout_session_id"] == checkout_session.id
    assert updated_payment.provider_data["checkout_session_status"] == checkout_session.status
    assert updated_payment.provider_data["checkout_session_payment_status"] == checkout_session.payment_status

    assert processed_event is not None
    assert processed_event.event_id == expired_checkout_session_event.id
    assert processed_event.event_type == "checkout.session.expired"
    assert processed_event.provider == "STRIPE"


async def test_process_checkout_session_expired_does_not_overwrite_non_pending_payment(
    process_checkout_session_expired_use_case: ProcessCheckoutSessionExpiredUseCase,
    expired_checkout_session_event,
    payment_service,
    pending_payment: Payment,
    test_transaction_manager: TransactionManager,
):
    async with test_transaction_manager:
        await payment_service.update_payment(
            pending_payment.id,
            status=PaymentStatusEnum.SUCCEEDED,
        )

    await process_checkout_session_expired_use_case.execute(expired_checkout_session_event)

    updated_payment = await payment_service.get_payment_by_id(str(pending_payment.id))
    processed_event = await payment_service.get_processed_webhook_event_by_kwargs(
        event_id=expired_checkout_session_event.id,
    )

    assert updated_payment.status == PaymentStatusEnum.SUCCEEDED
    assert processed_event is not None
