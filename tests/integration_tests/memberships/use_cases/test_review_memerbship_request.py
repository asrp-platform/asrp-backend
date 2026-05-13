from datetime import datetime, timedelta, timezone
from decimal import Decimal
from types import SimpleNamespace

import pytest

import app.domains.memberships.use_cases.review_membership_request as review_membership_request_module
from app.core.common.exceptions import PermissionDeniedError
from app.domains.memberships.exceptions import MissingMembershipRequestPayment, MissingRejectingCommentError
from app.domains.memberships.models import MembershipRequest, MembershipRequestStatusEnum
from app.domains.memberships.services import MembershipService, UserMembershipService
from app.domains.memberships.use_cases.review_membership_request import ReviewMembershipRequestUseCase
from app.domains.payments.models import PaymentProvider, PaymentPurposeEnum, PaymentStatusEnum
from app.domains.payments.services import PaymentService
from app.domains.shared.transaction_managers import TransactionManager
from app.domains.users.models import User

pytestmark = pytest.mark.anyio

MEMBERSHIP_DURATION = timedelta(days=365)


@pytest.fixture()
def test_review_membership_request_use_case(
    test_transaction_manager: TransactionManager,
    membership_service: MembershipService,
    user_membership_service: UserMembershipService,
    payment_service: PaymentService,
) -> ReviewMembershipRequestUseCase:
    return ReviewMembershipRequestUseCase(
        test_transaction_manager,
        membership_service,
        user_membership_service,
        payment_service,
    )


@pytest.fixture()
async def succeeded_membership_application_payment(
    test_transaction_manager: TransactionManager,
    paid_membership_request: MembershipRequest,
    test_user: User,
):
    async with test_transaction_manager:
        return await test_transaction_manager.payment_repository.create(
            provider=PaymentProvider.STRIPE,
            amount=Decimal("120.00"),
            status=PaymentStatusEnum.SUCCEEDED,
            purpose=PaymentPurposeEnum.MEMBERSHIP_APPLICATION,
            provider_data={"payment_intent_id": "pi_test_review_membership_request"},
            user_id=test_user.id,
            membership_request_id=paid_membership_request.id,
        )


async def test_approve_membership_request(
    test_transaction_manager: TransactionManager,
    admin_user: User,
    permissions_action_list: list[str],
    paid_membership_request: MembershipRequest,
    test_review_membership_request_use_case: ReviewMembershipRequestUseCase,
    test_user: User,
):
    before_review = datetime.now(timezone.utc)

    await test_review_membership_request_use_case.execute(
        paid_membership_request.id, admin_user, permissions_action_list, status=MembershipRequestStatusEnum.APPROVED
    )

    after_review = datetime.now(timezone.utc)

    async with test_transaction_manager:
        updated_request = await test_transaction_manager.membership_requests_repository.get_first_by_kwargs(
            id=paid_membership_request.id
        )
        created_user_membership = await test_transaction_manager.user_membership_repository.get_first_by_kwargs(
            membership_request_id=paid_membership_request.id
        )

    assert updated_request.status == MembershipRequestStatusEnum.APPROVED
    assert updated_request.reviewer_id == admin_user.id
    assert updated_request.reviewed_at is not None

    assert created_user_membership is not None
    assert created_user_membership.is_active
    assert created_user_membership.user_id == test_user.id
    assert created_user_membership.membership_request_id == paid_membership_request.id
    assert created_user_membership.membership_type_id == paid_membership_request.membership_type_id
    assert (
        before_review + MEMBERSHIP_DURATION <= created_user_membership.expires_at <= after_review + MEMBERSHIP_DURATION
    )


async def test_reject_membership_request_without_payment(
    test_transaction_manager: TransactionManager,
    admin_user: User,
    permissions_action_list: list[str],
    paid_membership_request: MembershipRequest,
    test_review_membership_request_use_case: ReviewMembershipRequestUseCase,
):
    admin_comment = "Application documents were not accepted"
    before_review = datetime.now(timezone.utc)

    await test_review_membership_request_use_case.execute(
        paid_membership_request.id,
        admin_user,
        permissions_action_list,
        status=MembershipRequestStatusEnum.REJECTED,
        admin_comment=admin_comment,
    )

    after_review = datetime.now(timezone.utc)

    async with test_transaction_manager:
        updated_request = await test_transaction_manager.membership_requests_repository.get_first_by_kwargs(
            id=paid_membership_request.id
        )
        created_user_membership = await test_transaction_manager.user_membership_repository.get_first_by_kwargs(
            membership_request_id=paid_membership_request.id
        )

    assert updated_request.status == MembershipRequestStatusEnum.REJECTED
    assert updated_request.reviewer_id == admin_user.id
    assert updated_request.admin_comment == admin_comment
    assert before_review <= updated_request.reviewed_at <= after_review

    assert created_user_membership is None


async def test_reject_membership_request_without_admin_comment(
    test_transaction_manager: TransactionManager,
    admin_user: User,
    permissions_action_list: list[str],
    paid_membership_request: MembershipRequest,
    test_review_membership_request_use_case: ReviewMembershipRequestUseCase,
):
    with pytest.raises(MissingRejectingCommentError):
        await test_review_membership_request_use_case.execute(
            paid_membership_request.id,
            admin_user,
            permissions_action_list,
            status=MembershipRequestStatusEnum.REJECTED,
        )

    async with test_transaction_manager:
        updated_request = await test_transaction_manager.membership_requests_repository.get_first_by_kwargs(
            id=paid_membership_request.id
        )
        created_user_membership = await test_transaction_manager.user_membership_repository.get_first_by_kwargs(
            membership_request_id=paid_membership_request.id
        )

    assert updated_request.status == MembershipRequestStatusEnum.PAID
    assert updated_request.reviewer_id is None
    assert updated_request.reviewed_at is None
    assert updated_request.admin_comment is None

    assert created_user_membership is None


async def test_reject_membership_request_with_succeeded_payment_creates_refund(
    test_transaction_manager: TransactionManager,
    admin_user: User,
    permissions_action_list: list[str],
    paid_membership_request: MembershipRequest,
    succeeded_membership_application_payment,
    test_review_membership_request_use_case: ReviewMembershipRequestUseCase,
    monkeypatch: pytest.MonkeyPatch,
):
    admin_comment = "Application rejected after manual review"
    stripe_refund = SimpleNamespace(
        id="re_test_review_membership_request",
        status="succeeded",
        amount=12000,
        currency="usd",
        reason="requested_by_customer",
        failure_reason=None,
    )

    monkeypatch.setattr(
        review_membership_request_module,
        "create_stripe_refund",
        lambda payment, idempotency_key: stripe_refund,
    )

    await test_review_membership_request_use_case.execute(
        paid_membership_request.id,
        admin_user,
        permissions_action_list,
        status=MembershipRequestStatusEnum.REJECTED,
        admin_comment=admin_comment,
    )

    async with test_transaction_manager:
        updated_request = await test_transaction_manager.membership_requests_repository.get_first_by_kwargs(
            id=paid_membership_request.id
        )
        updated_payment = await test_transaction_manager.payment_repository.get_first_by_kwargs(
            id=succeeded_membership_application_payment.id
        )
        created_user_membership = await test_transaction_manager.user_membership_repository.get_first_by_kwargs(
            membership_request_id=paid_membership_request.id
        )

    assert updated_request.status == MembershipRequestStatusEnum.REJECTED
    assert updated_request.reviewer_id == admin_user.id
    assert updated_request.admin_comment == admin_comment

    assert updated_payment.status == PaymentStatusEnum.REFUNDED
    assert updated_payment.provider_data["refund"] == {
        "id": stripe_refund.id,
        "status": stripe_refund.status,
        "amount": stripe_refund.amount,
        "currency": stripe_refund.currency,
        "reason": stripe_refund.reason,
        "failure_reason": stripe_refund.failure_reason,
        "idempotency_key": f"refund-payment-{succeeded_membership_application_payment.id}",
    }

    assert created_user_membership is None


async def test_reject_unpaid_membership_request(
    test_transaction_manager: TransactionManager,
    admin_user: User,
    permissions_action_list: list[str],
    user_membership_request: MembershipRequest,
    test_review_membership_request_use_case: ReviewMembershipRequestUseCase,
) -> None:
    with pytest.raises(MissingMembershipRequestPayment):
        await test_review_membership_request_use_case.execute(
            user_membership_request.id,
            admin_user,
            permissions_action_list,
            status=MembershipRequestStatusEnum.REJECTED,
            admin_comment="Application rejected",
        )

    async with test_transaction_manager:
        user_membership = await test_transaction_manager.user_membership_repository.get_first_by_kwargs(
            membership_request_id=user_membership_request.id
        )

    assert user_membership is None


async def test_approve_unpaid_membership_request(
    test_transaction_manager: TransactionManager,
    admin_user: User,
    permissions_action_list: list[str],
    user_membership_request: MembershipRequest,
    test_review_membership_request_use_case: ReviewMembershipRequestUseCase,
) -> None:
    with pytest.raises(MissingMembershipRequestPayment):
        await test_review_membership_request_use_case.execute(
            user_membership_request.id, admin_user, permissions_action_list, status=MembershipRequestStatusEnum.APPROVED
        )

    async with test_transaction_manager:
        user_membership = await test_transaction_manager.user_membership_repository.get_first_by_kwargs(
            membership_request_id=user_membership_request.id
        )
    assert user_membership is None


async def test_execute_no_permissions(
    test_transaction_manager: TransactionManager,
    admin_user: User,
    permissions_action_list: list[str],
    paid_membership_request: MembershipRequest,
    test_review_membership_request_use_case: ReviewMembershipRequestUseCase,
) -> None:
    permissions = [permission for permission in permissions_action_list if permission != "memberships.update"]

    with pytest.raises(PermissionDeniedError):
        await test_review_membership_request_use_case.execute(
            paid_membership_request.id, admin_user, permissions, status=MembershipRequestStatusEnum.APPROVED
        )

    async with test_transaction_manager:
        user_membership = await test_transaction_manager.user_membership_repository.get_first_by_kwargs(
            membership_request_id=paid_membership_request.id
        )
    assert user_membership is None
