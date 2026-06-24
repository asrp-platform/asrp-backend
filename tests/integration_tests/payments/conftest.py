from types import SimpleNamespace

import pytest
from faker import Faker

from app.domains.memberships.models import MembershipRequest, MembershipRequestStatusEnum
from app.domains.memberships.services import MembershipRequestService
from app.domains.payments.models import Payment, PaymentProvider, PaymentPurposeEnum, PaymentStatusEnum
from app.domains.payments.purpose_handlers.membership_application import MembershipApplicationHandler
from app.domains.payments.purpose_handlers.membership_renewal import MembershipRenewalHandler
from app.domains.payments.purpose_handlers.registry import PaymentPurposeHandlerRegistry
from app.domains.payments.services import PaymentService
from app.domains.payments.use_cases.process_payment_event import ProcessPaymentUseCase
from app.domains.shared.transaction_managers import TransactionManager
from app.domains.users.models import User


@pytest.fixture()
def process_payment_use_case(
    test_transaction_manager: TransactionManager,
    payment_service,
    membership_service,
    user_membership_service,
    user_service,
    email_queue,
):
    membership_application_handler = MembershipApplicationHandler(
        membership_service=membership_service,
        payment_service=payment_service,
        email_queue=email_queue,
        user_service=user_service,
    )
    membership_renewal_handler = MembershipRenewalHandler(
        user_membership_service=user_membership_service,
        payment_service=payment_service,
    )
    payment_purpose_handler_registry = PaymentPurposeHandlerRegistry(
        membership_application_handler=membership_application_handler,
        membership_renewal_handler=membership_renewal_handler,
    )
    return ProcessPaymentUseCase(
        transaction_manager=test_transaction_manager,
        payment_service=payment_service,
        membership_service=membership_service,
        payment_purpose_handler_registry=payment_purpose_handler_registry,
    )


@pytest.fixture()
async def membership_request_payment_pending(
    test_user: User,
    membership_service: MembershipRequestService,
    membership_request_create_data,
):
    membership_request = await membership_service.create_membership_request(
        test_user.id,
        membership_request_create_data["membership_type"],
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
        await test_transaction_manager.flush()
        payment = await test_transaction_manager.payment_repository.create(
            provider=PaymentProvider.STRIPE,
            amount=2000,
            status=PaymentStatusEnum.PENDING,
            purpose=PaymentPurposeEnum.MEMBERSHIP_APPLICATION,
            user_id=test_user.id,
            membership_request_id=membership_request_payment_pending.id,
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

    return SimpleNamespace(
        id=event_id,
        type="payment_intent.succeeded",
        data=SimpleNamespace(
            object=payment_intent,
        ),
    )
