from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from faker import Faker

import app.domains.users.use_cases.current_user_membership.reapply_membership_application as reapply_module
from app.core.common.exceptions import NotFoundError
from app.domains.memberships.exceptions import (
    MembershipAlreadyPaidError,
    MembershipApplicationCheckoutError,
    MembershipRequestCannotBeReappliedError,
)
from app.domains.memberships.models import MembershipRequest, MembershipRequestStatusEnum
from app.domains.memberships.services import MembershipRequestService, MembershipTypeService
from app.domains.payments.models import PaymentProvider, PaymentPurposeEnum, PaymentStatusEnum
from app.domains.payments.services import PaymentService
from app.domains.shared.transaction_managers import TransactionManager
from app.domains.users.models import User
from app.domains.users.use_cases.current_user_membership.reapply_membership_application import (
    ReapplyMembershipApplicationUseCase,
)


pytestmark = pytest.mark.anyio


class LoggerSpy:
    def __init__(self):
        self.info_calls = []
        self.exception_calls = []

    def info(self, message, *args):
        self.info_calls.append((message, args))

    def exception(self, message, *args):
        self.exception_calls.append((message, args))


@pytest.fixture()
def reapply_use_case(
    test_transaction_manager: TransactionManager,
    membership_service: MembershipRequestService,
    membership_type_service: MembershipTypeService,
    payment_service: PaymentService,
) -> ReapplyMembershipApplicationUseCase:
    return ReapplyMembershipApplicationUseCase(
        test_transaction_manager,
        membership_service,
        membership_type_service,
        payment_service,
    )


@pytest.fixture()
def logger_spy(monkeypatch: pytest.MonkeyPatch) -> LoggerSpy:
    logger = LoggerSpy()
    monkeypatch.setattr(reapply_module, "payments_logger", logger)
    return logger


@pytest.fixture()
def reapply_data(faker: Faker) -> dict:
    return {
        "primary_affiliation": faker.company(),
        "job_title": faker.job(),
        "practice_setting": faker.word(),
        "subspecialty": faker.word(),
    }


async def test_reapply_membership_application_creates_checkout_and_logs(
    test_transaction_manager: TransactionManager,
    reapply_use_case: ReapplyMembershipApplicationUseCase,
    rejected_membership_request: MembershipRequest,
    purchasable_membership_type_id: int,
    test_user: User,
    reapply_data: dict,
    logger_spy: LoggerSpy,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    checkout_session = SimpleNamespace(
        id="cs_reapply_success",
        status="open",
        payment_status="unpaid",
        url="https://checkout.stripe.com/reapply-success",
    )

    async def create_checkout_session_mock(*, membership_request, membership_type, payment, customer_email):
        assert customer_email == test_user.email
        return SimpleNamespace(
            session=checkout_session,
            provider_data={
                "membership_request_id": membership_request.id,
                "payment_id": str(payment.id),
                "checkout_session_id": checkout_session.id,
                "checkout_session_status": checkout_session.status,
                "payment_intent_status": checkout_session.payment_status,
                "url": checkout_session.url,
            },
        )

    create_checkout_session = AsyncMock(side_effect=create_checkout_session_mock)
    monkeypatch.setattr(
        reapply_module,
        "create_membership_application_checkout_session",
        create_checkout_session,
    )

    result = await reapply_use_case.execute(
        test_user,
        membership_type_id=purchasable_membership_type_id,
        **reapply_data,
    )

    async with test_transaction_manager:
        membership_request = await test_transaction_manager.membership_requests_repository.get_first_by_kwargs(
            id=rejected_membership_request.id,
        )
        payment = await test_transaction_manager.payment_repository.get_first_by_kwargs(
            membership_request_id=rejected_membership_request.id,
            purpose=PaymentPurposeEnum.MEMBERSHIP_APPLICATION,
        )

    assert result == checkout_session.url
    assert membership_request.status == MembershipRequestStatusEnum.PAYMENT_PENDING
    assert membership_request.reviewer_id is None
    assert membership_request.reviewed_at is None
    assert membership_request.admin_comment is None
    assert membership_request.membership_type_id == purchasable_membership_type_id
    assert membership_request.primary_affiliation == reapply_data["primary_affiliation"]

    assert payment.status == PaymentStatusEnum.PENDING
    assert payment.provider == PaymentProvider.STRIPE
    assert payment.provider_data["checkout_session_id"] == checkout_session.id

    assert create_checkout_session.await_count == 1
    logged_messages = [message for message, _ in logger_spy.info_calls]
    assert "Membership request reapply started: user_id={}" in logged_messages
    assert "Created membership reapply payment intent: membership_request_id={} payment_id={}" in logged_messages
    assert (
        "Created membership request reapply: membership_request_id={} payment_id={} checkout_session_id={}"
        in logged_messages
    )


async def test_reapply_membership_application_fails_when_request_not_found(
    reapply_use_case: ReapplyMembershipApplicationUseCase,
    test_user: User,
    reapply_data: dict,
    purchasable_membership_type_id: int,
) -> None:
    with pytest.raises(NotFoundError):
        await reapply_use_case.execute(
            test_user,
            membership_type_id=purchasable_membership_type_id,
            **reapply_data,
        )


async def test_reapply_membership_application_fails_when_request_not_rejected(
    reapply_use_case: ReapplyMembershipApplicationUseCase,
    user_membership_request: MembershipRequest,
    test_user: User,
    reapply_data: dict,
    purchasable_membership_type_id: int,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    create_checkout_session = AsyncMock()
    monkeypatch.setattr(
        reapply_module,
        "create_membership_application_checkout_session",
        create_checkout_session,
    )

    with pytest.raises(MembershipRequestCannotBeReappliedError):
        await reapply_use_case.execute(
            test_user,
            membership_type_id=purchasable_membership_type_id,
            **reapply_data,
        )

    create_checkout_session.assert_not_awaited()


async def test_reapply_membership_application_fails_when_succeeded_payment_exists(
    test_transaction_manager: TransactionManager,
    reapply_use_case: ReapplyMembershipApplicationUseCase,
    rejected_membership_request: MembershipRequest,
    test_user: User,
    reapply_data: dict,
    purchasable_membership_type_id: int,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async with test_transaction_manager:
        await test_transaction_manager.payment_repository.create(
            provider=PaymentProvider.STRIPE,
            amount=2000,
            status=PaymentStatusEnum.SUCCEEDED,
            purpose=PaymentPurposeEnum.MEMBERSHIP_APPLICATION,
            user_id=test_user.id,
            provider_data={"payment_intent_id": "pi_reapply_succeeded"},
            membership_request_id=rejected_membership_request.id,
        )

    create_checkout_session = AsyncMock()
    monkeypatch.setattr(
        reapply_module,
        "create_membership_application_checkout_session",
        create_checkout_session,
    )

    with pytest.raises(MembershipAlreadyPaidError):
        await reapply_use_case.execute(
            test_user,
            membership_type_id=purchasable_membership_type_id,
            **reapply_data,
        )

    create_checkout_session.assert_not_awaited()


async def test_reapply_membership_application_marks_payment_failed_when_checkout_creation_fails(
    test_transaction_manager: TransactionManager,
    reapply_use_case: ReapplyMembershipApplicationUseCase,
    rejected_membership_request: MembershipRequest,
    test_user: User,
    reapply_data: dict,
    purchasable_membership_type_id: int,
    logger_spy: LoggerSpy,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    create_checkout_session = AsyncMock(side_effect=RuntimeError("stripe is down"))
    monkeypatch.setattr(
        reapply_module,
        "create_membership_application_checkout_session",
        create_checkout_session,
    )

    with pytest.raises(MembershipApplicationCheckoutError):
        await reapply_use_case.execute(
            test_user,
            membership_type_id=purchasable_membership_type_id,
            **reapply_data,
        )

    async with test_transaction_manager:
        payments, _ = await test_transaction_manager.payment_repository.list(
            filters={
                "membership_request_id": rejected_membership_request.id,
                "purpose": PaymentPurposeEnum.MEMBERSHIP_APPLICATION,
            },
        )
        membership_request = await test_transaction_manager.membership_requests_repository.get_first_by_kwargs(
            id=rejected_membership_request.id,
        )

    assert len(payments) == 1
    assert payments[0].status == PaymentStatusEnum.FAILED
    assert payments[0].provider_data["error_type"] == "checkout_session_error"
    assert membership_request.status == MembershipRequestStatusEnum.PAYMENT_PENDING
    assert create_checkout_session.await_count == 1
    assert logger_spy.exception_calls == [
        (
            "Failed to create reapply checkout session: membership_request_id={} payment_id={}",
            (rejected_membership_request.id, payments[0].id),
        )
    ]
