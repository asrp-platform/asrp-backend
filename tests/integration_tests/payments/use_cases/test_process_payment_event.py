from types import SimpleNamespace

import pytest
from faker import Faker

from app.domains.memberships.models import MembershipRequest, MembershipRequestStatusEnum, MembershipTypeEnum
from app.domains.memberships.services import MembershipService
from app.domains.payments.models import Payment, PaymentProvider, PaymentPurposeEnum, PaymentStatusEnum
from app.domains.payments.services import PaymentService
from app.domains.payments.use_cases.process_payment_event import ProcessPaymentUseCase
from app.domains.shared.transaction_managers import TransactionManager
from app.domains.users.models import User

pytestmark = pytest.mark.anyio


@pytest.fixture(scope="function")
def membership_request_create_data(faker: Faker) -> dict:
    return {
        "membership": {
            "primary_affiliation": faker.company(),
            "job_title": faker.job(),
            "practice_setting": faker.word(),
            "subspecialty": faker.word(),
        },
        "membership_type": faker.random_element([item for item in MembershipTypeEnum]),
        "feedback_additional_info": {
            "hear_about_asrp": faker.sentence(),
            "tg_username": f"@{faker.user_name()[:20]}",
            "interest_description": faker.text(max_nb_chars=200),
        },
        "is_agrees_communications": faker.boolean(),
    }


@pytest.fixture()
def process_payment_use_case(
    test_transaction_manager: TransactionManager,
    payment_service,
    membership_service,
):
    return ProcessPaymentUseCase(
        transaction_manager=test_transaction_manager,
        payment_service=payment_service,
        membership_service=membership_service,
    )


@pytest.fixture()
async def membership_request_payment_pending(
    faker: Faker,
    test_user: User,
    membership_service: MembershipService,
    membership_request_create_data,
):
    membership_request = await membership_service.create_membership_request(
        test_user.id,
        faker.random_element([item for item in MembershipTypeEnum]),
        status=MembershipRequestStatusEnum.PAYMENT_PENDING,
        **membership_request_create_data["membership"],
    )
    return membership_request


@pytest.fixture()
async def pending_payment(
    faker: Faker,
    test_transaction_manager: TransactionManager,
    test_user: User,
    payment_service: PaymentService,
    membership_request_payment_pending: MembershipRequest,
):
    async with test_transaction_manager:
        payment = await test_transaction_manager.payment_repository.create(
            provider=PaymentProvider.STRIPE,
            amount=2000,  # cents
            status=PaymentStatusEnum.PENDING,
            purpose=PaymentPurposeEnum.MEMBERSHIP_APPLICATION,
            user_id=test_user.id,
            provider_data=None,
        )
        await test_transaction_manager._session.flush()
        provider_data = {
            "membership_request_id": membership_request_payment_pending.id,
            "payment_id": str(payment.id),
            "checkout_session_id": f"cs_test_{faker.uuid4()}",
            "checkout_session_status": "complete",
            "payment_intent_status": "requires_payment_method",
            "url": "https://checkout.stripe.com/test",
        }
        payment = await test_transaction_manager.payment_repository.update(
            payment.id,
            provider_data=provider_data,
        )
        return payment


@pytest.fixture()
def stripe_event(
    faker: Faker,
    pending_payment: Payment,
    membership_request_payment_pending: MembershipRequest,
):
    event_id = f"evt_{faker.uuid4()}"
    payment_intent_id = f"pi_{faker.uuid4()}"

    payment_intent = SimpleNamespace(
        id=payment_intent_id,
        status="succeeded",
        metadata=SimpleNamespace(
            payment_id=str(pending_payment.id),
            membership_request_id=str(membership_request_payment_pending.id),
        ),
    )

    return {
        "id": event_id,
        "type": "payment_intent.succeeded",
        "data": {
            "object": payment_intent,
        },
    }


async def test_process_payment_event_succeeded(
    process_payment_use_case,
    stripe_event,
    membership_service,
    payment_service,
    pending_payment: Payment,
    membership_request_payment_pending: MembershipRequest,
):
    await process_payment_use_case.execute(
        event=stripe_event,
        target_payment_status=PaymentStatusEnum.SUCCEEDED,
    )

    payment_intent = stripe_event["data"]["object"]
    event_id = stripe_event["id"]

    updated_payment = await payment_service.get_payment_by_id(str(pending_payment.id))
    processed_event = await payment_service.get_processed_webhook_event_by_kwargs(
        event_id=event_id,
    )
    updated_membership_request = await membership_service.get_membership_request_by_id(
        membership_request_payment_pending.id,
    )

    assert updated_payment is not None
    assert updated_payment.id == pending_payment.id
    assert updated_payment.status == PaymentStatusEnum.SUCCEEDED

    assert updated_payment.provider_data["membership_request_id"] == membership_request_payment_pending.id
    assert updated_payment.provider_data["payment_id"] == str(pending_payment.id)
    assert updated_payment.provider_data["payment_intent_id"] == payment_intent.id
    assert updated_payment.provider_data["payment_intent_status"] == payment_intent.status

    assert processed_event is not None
    assert processed_event.event_id == event_id
    assert processed_event.event_type == "payment_intent.succeeded"
    assert processed_event.provider == "STRIPE"

    assert updated_membership_request.status == MembershipRequestStatusEnum.PAYMENT_PENDING


async def test_process_payment_event_failed(
    process_payment_use_case,
    stripe_event,
    membership_service,
    payment_service,
    pending_payment: Payment,
    membership_request_payment_pending: MembershipRequest,
):
    await process_payment_use_case.execute(
        event=stripe_event,
        target_payment_status=PaymentStatusEnum.FAILED,
    )

    payment_intent = stripe_event["data"]["object"]
    event_id = stripe_event["id"]

    updated_payment = await payment_service.get_payment_by_id(str(pending_payment.id))
    processed_event = await payment_service.get_processed_webhook_event_by_kwargs(
        event_id=event_id,
    )
    updated_membership_request = await membership_service.get_membership_request_by_id(
        membership_request_payment_pending.id,
    )

    assert updated_payment is not None
    assert updated_payment.id == pending_payment.id
    assert updated_payment.status == PaymentStatusEnum.FAILED

    assert updated_payment.provider_data["membership_request_id"] == membership_request_payment_pending.id
    assert updated_payment.provider_data["payment_id"] == str(pending_payment.id)
    assert updated_payment.provider_data["payment_intent_id"] == payment_intent.id
    assert updated_payment.provider_data["payment_intent_status"] == payment_intent.status

    assert processed_event is not None
    assert processed_event.event_id == event_id
    assert processed_event.event_type == "payment_intent.succeeded"
    assert processed_event.provider == "STRIPE"

    assert updated_membership_request.status == MembershipRequestStatusEnum.PAYMENT_FAILED
