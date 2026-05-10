from datetime import datetime, timedelta, timezone

import pytest

from app.core.common.exceptions import PermissionDeniedError
from app.domains.memberships.exceptions import MissingMembershipRequestPayment
from app.domains.memberships.models import MembershipRequest, MembershipRequestStatusEnum
from app.domains.memberships.services import MembershipService, UserMembershipService
from app.domains.memberships.use_cases.review_membership_request import ReviewMembershipRequestUseCase
from app.domains.payments.services import PaymentService
from app.domains.shared.transaction_managers import TransactionManager
from app.domains.users.models import User

pytestmark = pytest.mark.anyio


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

    updated_request = await test_transaction_manager.membership_requests_repository.get_first_by_kwargs(
        id=paid_membership_request.id
    )
    created_user_membership = await test_transaction_manager.user_membership_repository.get_first_by_kwargs(
        membership_request_id=paid_membership_request.id
    )

    assert updated_request.status == MembershipRequestStatusEnum.APPROVED
    assert updated_request.reviewer_id == admin_user.id

    assert created_user_membership is not None
    assert created_user_membership.is_active
    assert created_user_membership.membership_type_id == paid_membership_request.membership_type_id
    assert (
        before_review + timedelta(days=365) <= created_user_membership.expires_at <= after_review + timedelta(days=365)
    )


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
    # вызывается корректная ошибка
    # UserMembership не создается
    permissions_action_list.remove("memberships.update")

    with pytest.raises(PermissionDeniedError):
        await test_review_membership_request_use_case.execute(
            paid_membership_request.id, admin_user, permissions_action_list, status=MembershipRequestStatusEnum.APPROVED
        )

    user_membership = await test_transaction_manager.user_membership_repository.get_first_by_kwargs(
        membership_request_id=paid_membership_request.id
    )
    assert user_membership is None
