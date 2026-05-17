from unittest.mock import AsyncMock, patch

import pytest

from app.domains.memberships.exceptions import MembershipAlreadyPaidError, MembershipApplicationCheckoutError
from app.domains.memberships.use_cases.create_membership_application_payment_attempt import (
    CreateMembershipApplicationPaymentAttemptUseCase,
)
from app.domains.payments.models import PaymentProvider, PaymentPurposeEnum, PaymentStatusEnum
from app.domains.shared.transaction_managers import TransactionManager
from app.domains.users.models import User

pytestmark = pytest.mark.anyio


@pytest.fixture()
def test_create_membership_application_payment_attempt_use_case(
    test_transaction_manager: TransactionManager,
    membership_service,
    payment_service,
):
    return CreateMembershipApplicationPaymentAttemptUseCase(
        test_transaction_manager,
        membership_service,
        payment_service,
    )


async def test_create_membership_application_payment_attempt_fails_when_successful_payment_exists(
    test_transaction_manager: TransactionManager,
    test_create_membership_application_payment_attempt_use_case: CreateMembershipApplicationPaymentAttemptUseCase,
    test_user: User,
    payment_pending_membership_request,
):
    async with test_transaction_manager:
        await test_transaction_manager.payment_repository.create(
            provider=PaymentProvider.STRIPE,
            amount=2000,
            status=PaymentStatusEnum.SUCCEEDED,
            purpose=PaymentPurposeEnum.MEMBERSHIP_APPLICATION,
            user_id=test_user.id,
            provider_data=None,
            membership_request_id=payment_pending_membership_request.id,
        )

    with (
        patch(
            "app.domains.memberships.use_cases.create_membership_application_payment_attempt.create_membership_application_checkout_session",
            new=AsyncMock(),
        ) as create_membership_application_checkout_session_mock,
        pytest.raises(MembershipAlreadyPaidError),
    ):
        await test_create_membership_application_payment_attempt_use_case.execute(test_user)

    create_membership_application_checkout_session_mock.assert_not_awaited()


async def test_create_membership_application_payment_attempt_marks_payment_failed_when_checkout_creation_fails(
    test_transaction_manager: TransactionManager,
    test_create_membership_application_payment_attempt_use_case: CreateMembershipApplicationPaymentAttemptUseCase,
    test_user: User,
    user_membership_request,
):
    with (
        patch(
            "app.domains.memberships.use_cases.create_membership_application_payment_attempt.create_membership_application_checkout_session",
            new=AsyncMock(side_effect=RuntimeError("stripe is down")),
        ) as create_membership_application_checkout_session_mock,
        pytest.raises(MembershipApplicationCheckoutError),
    ):
        await test_create_membership_application_payment_attempt_use_case.execute(test_user)

    async with test_transaction_manager:
        payment = await test_transaction_manager.payment_repository.get_first_by_kwargs(
            user_id=test_user.id,
            purpose=PaymentPurposeEnum.MEMBERSHIP_APPLICATION,
        )

    assert create_membership_application_checkout_session_mock.await_count == 1
    assert payment.status == PaymentStatusEnum.FAILED
    assert payment.provider_data["error_type"] == "checkout_session_error"
