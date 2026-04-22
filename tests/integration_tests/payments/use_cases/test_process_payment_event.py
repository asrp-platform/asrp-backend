import pytest

from app.domains.memberships.models import MembershipRequest, MembershipRequestStatusEnum
from app.domains.payments.models import Payment, PaymentStatusEnum
from app.domains.shared.transaction_managers import TransactionManager

pytestmark = pytest.mark.anyio


@pytest.mark.parametrize(
    ("target_payment_status", "expected_membership_request_status"),
    [
        (PaymentStatusEnum.SUCCEEDED, MembershipRequestStatusEnum.PAYMENT_PENDING),
        (PaymentStatusEnum.FAILED, MembershipRequestStatusEnum.PAYMENT_FAILED),
    ],
)
async def test_process_payment_event(
    process_payment_use_case,
    stripe_event,
    membership_service,
    payment_service,
    pending_payment: Payment,
    membership_request_payment_pending: MembershipRequest,
    target_payment_status: PaymentStatusEnum,
    expected_membership_request_status: MembershipRequestStatusEnum,
):
    await process_payment_use_case.execute(
        event=stripe_event,
        target_payment_status=target_payment_status,
    )

    payment_intent = stripe_event.data.object
    event_id = stripe_event.id

    updated_payment = await payment_service.get_payment_by_id(str(pending_payment.id))
    processed_event = await payment_service.get_processed_webhook_event_by_kwargs(
        event_id=event_id,
    )
    updated_membership_request = await membership_service.get_membership_request_by_id(
        membership_request_payment_pending.id,
    )

    assert updated_payment is not None
    assert updated_payment.id == pending_payment.id
    assert updated_payment.status == target_payment_status

    assert updated_payment.provider_data["membership_request_id"] == membership_request_payment_pending.id
    assert updated_payment.provider_data["payment_id"] == str(pending_payment.id)
    assert updated_payment.provider_data["payment_intent_id"] == payment_intent.id
    assert updated_payment.provider_data["payment_intent_status"] == payment_intent.status

    assert processed_event is not None
    assert processed_event.event_id == event_id
    assert processed_event.event_type == "payment_intent.succeeded"
    assert processed_event.provider == "STRIPE"

    assert updated_membership_request.status == expected_membership_request_status


@pytest.mark.parametrize(
    ("target_payment_status", "expected_membership_request_status"),
    [
        (PaymentStatusEnum.SUCCEEDED, MembershipRequestStatusEnum.PAYMENT_PENDING),
        (PaymentStatusEnum.FAILED, MembershipRequestStatusEnum.PAYMENT_FAILED),
    ],
)
async def test_process_payment_event_is_idempotent(
    process_payment_use_case,
    stripe_event,
    membership_service,
    payment_service,
    test_transaction_manager: TransactionManager,
    pending_payment: Payment,
    membership_request_payment_pending: MembershipRequest,
    target_payment_status: PaymentStatusEnum,
    expected_membership_request_status: MembershipRequestStatusEnum,
):
    await process_payment_use_case.execute(
        event=stripe_event,
        target_payment_status=target_payment_status,
    )

    first_payment = await payment_service.get_payment_by_id(str(pending_payment.id))
    first_processed_event = await payment_service.get_processed_webhook_event_by_kwargs(
        event_id=stripe_event.id,
    )
    first_membership_request = await membership_service.get_membership_request_by_id(
        membership_request_payment_pending.id,
    )

    await process_payment_use_case.execute(
        event=stripe_event,
        target_payment_status=target_payment_status,
    )

    second_payment = await payment_service.get_payment_by_id(str(pending_payment.id))
    second_processed_event = await payment_service.get_processed_webhook_event_by_kwargs(
        event_id=stripe_event.id,
    )
    second_membership_request = await membership_service.get_membership_request_by_id(
        membership_request_payment_pending.id,
    )

    async with test_transaction_manager:
        (
            processed_events,
            processed_events_count,
        ) = await test_transaction_manager.processed_webhook_event_repository.list(
            filters={"event_id": stripe_event.id},
        )

    assert first_payment is not None
    assert second_payment is not None
    assert first_payment.status == target_payment_status
    assert second_payment.status == target_payment_status
    assert first_payment.provider_data == second_payment.provider_data

    assert first_processed_event is not None
    assert second_processed_event is not None
    assert first_processed_event.id == second_processed_event.id
    assert processed_events_count == 1
    assert len(processed_events) == 1

    assert first_membership_request.status == expected_membership_request_status
    assert second_membership_request.status == expected_membership_request_status
