from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import pytest
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.domains.memberships.models import MembershipRequest, MembershipRequestStatusEnum
from app.domains.memberships.use_cases.create_membership_request import CreateUserMembershipRequestUseCase
from app.domains.payments.models import PaymentPurposeEnum, PaymentStatusEnum
from app.domains.shared.transaction_managers import TransactionManager
from app.domains.users.models import User

pytestmark = pytest.mark.anyio


@pytest.fixture()
def test_create_user_membership_use_case(
    test_transaction_manager: TransactionManager,
    membership_service,
    feedback_additional_info_service,
    communication_preference_service,
    payment_service,
):
    return CreateUserMembershipRequestUseCase(
        test_transaction_manager,
        membership_service,
        feedback_additional_info_service,
        communication_preference_service,
        payment_service,
    )


async def test_create_user_membership_request(
    test_transaction_manager: TransactionManager,
    test_create_user_membership_use_case: CreateUserMembershipRequestUseCase,
    test_user: User,
    membership_request_create_data,
):
    is_agrees_communications = membership_request_create_data["is_agrees_communications"]
    membership_type = membership_request_create_data["membership_type"]
    membership = membership_request_create_data["membership"]
    feedback_additional_info = membership_request_create_data["feedback_additional_info"]

    fake_checkout_session = SimpleNamespace(
        id="cs_test_123",
        status="open",
        payment_status="unpaid",
        url="https://checkout.stripe.com/test-session",
    )

    with patch(
        "app.domains.memberships.use_cases.create_membership_request.create_checkout_session",
        new=AsyncMock(return_value=fake_checkout_session),
    ):
        result = await test_create_user_membership_use_case.execute(
            user_id=test_user.id,
            is_agrees_communications=is_agrees_communications,
            membership_type=membership_type,
            membership_request_data=membership,
            feedback_additional_info_data=feedback_additional_info,
        )

    stmt = select(MembershipRequest).options(selectinload(MembershipRequest.membership_type))
    membership_request = await test_transaction_manager.membership_requests_repository.get_first_by_kwargs(
        stmt=stmt,
        user_id=test_user.id,
    )
    payment = await test_transaction_manager.payment_repository.get_first_by_kwargs(
        user_id=test_user.id,
        purpose=PaymentPurposeEnum.MEMBERSHIP_APPLICATION,
    )
    feedback = await test_transaction_manager.feedback_additional_info_repository.get_first_by_kwargs(
        user_id=test_user.id,
    )
    communication_preferences = await test_transaction_manager.communication_preferences_repository.get_first_by_kwargs(
        user_id=test_user.id,
    )

    assert result == "https://checkout.stripe.com/test-session"

    assert payment is not None
    assert payment.user_id == test_user.id
    assert payment.status == PaymentStatusEnum.PENDING
    assert payment.purpose == PaymentPurposeEnum.MEMBERSHIP_APPLICATION
    assert payment.provider_data is not None
    assert payment.provider_data["payment_id"] == str(payment.id)
    assert payment.provider_data["membership_request_id"] == membership_request.id
    assert payment.provider_data["checkout_session_id"] == "cs_test_123"

    assert membership_request is not None
    assert membership_request.status == MembershipRequestStatusEnum.PAYMENT_PENDING
    assert membership_request.membership_type.type == membership_type

    assert feedback is not None
    assert feedback.hear_about_asrp == feedback_additional_info["hear_about_asrp"]
    assert feedback.tg_username == feedback_additional_info["tg_username"]
    assert feedback.interest_description == feedback_additional_info["interest_description"]

    assert communication_preferences is not None
    assert communication_preferences.user_id == test_user.id

    if is_agrees_communications:
        assert communication_preferences.newsletters
        assert communication_preferences.events_meetings
        assert communication_preferences.committees_leadership
        assert communication_preferences.volunteer_opportunities
