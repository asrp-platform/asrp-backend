from datetime import datetime, timedelta, timezone

import pytest

from app.domains.memberships.models import MembershipType, UserMembership
from app.domains.memberships.schemas.user_memberships import (
    MembershipHistoryEventTypeEnum,
    MembershipStatusEnum,
)
from app.domains.memberships.services import (
    MembershipDowngradeService,
    MembershipRequestService,
    MembershipTypeService,
    UserMembershipService,
)
from app.domains.payments.models import PaymentProvider, PaymentPurposeEnum, PaymentStatusEnum
from app.domains.payments.services import PaymentService
from app.domains.shared.transaction_managers import TransactionManager
from app.domains.users.models import User
from app.domains.users.use_cases.current_user_membership.get_membership_confirmation_report import (
    GetMembershipConfirmationReportUseCase,
)


pytestmark = pytest.mark.anyio


def _build_use_case(transaction_manager: TransactionManager) -> GetMembershipConfirmationReportUseCase:
    return GetMembershipConfirmationReportUseCase(
        transaction_manager=transaction_manager,
        user_membership_service=UserMembershipService(transaction_manager),
        membership_request_service=MembershipRequestService(transaction_manager),
        membership_type_service=MembershipTypeService(transaction_manager),
        membership_type_change_service=MembershipDowngradeService(transaction_manager),
        payment_service=PaymentService(transaction_manager),
    )


async def test_builds_active_membership_report_from_database_labels(
    test_transaction_manager: TransactionManager,
    test_user: User,
    purchasable_membership_type: MembershipType,
    user_membership: UserMembership,
) -> None:
    report = await _build_use_case(test_transaction_manager).execute(test_user)

    assert report.member_name == test_user.full_name
    assert report.membership_type == purchasable_membership_type.name
    assert report.status == MembershipStatusEnum.ACTIVE
    assert report.member_since == user_membership.created_at
    assert report.valid_through == user_membership.expires_at
    assert len(report.history) == 1
    assert report.history[0].event_type == MembershipHistoryEventTypeEnum.ACTIVATED
    assert report.history[0].membership_type == purchasable_membership_type.name


async def test_report_status_prefers_termination_and_includes_restriction_history(
    test_transaction_manager: TransactionManager,
    test_user: User,
    user_membership: UserMembership,
) -> None:
    now = datetime.now(timezone.utc)
    suspended_at = user_membership.created_at + timedelta(seconds=1)
    terminated_at = user_membership.created_at + timedelta(seconds=2)
    async with test_transaction_manager:
        await test_transaction_manager.user_membership_repository.update(
            user_membership.id,
            suspended_at=suspended_at,
            suspended_until=now + timedelta(days=5),
            suspension_reason="Membership review",
            terminated=True,
            terminated_at=terminated_at,
            termination_reason="Membership terminated",
        )

    report = await _build_use_case(test_transaction_manager).execute(test_user)

    assert report.status == MembershipStatusEnum.TERMINATED
    assert [event.event_type for event in report.history[-2:]] == [
        MembershipHistoryEventTypeEnum.SUSPENDED,
        MembershipHistoryEventTypeEnum.TERMINATED,
    ]
    assert report.history[-2].reason == "Membership review"
    assert report.history[-1].reason == "Membership terminated"


async def test_report_marks_current_suspension(
    test_transaction_manager: TransactionManager,
    test_user: User,
    user_membership: UserMembership,
) -> None:
    async with test_transaction_manager:
        await test_transaction_manager.user_membership_repository.update(
            user_membership.id,
            suspended_at=user_membership.created_at + timedelta(seconds=1),
            suspended_until=datetime.now(timezone.utc) + timedelta(days=5),
            suspension_reason="Membership review",
        )

    report = await _build_use_case(test_transaction_manager).execute(test_user)

    assert report.status == MembershipStatusEnum.SUSPENDED


async def test_report_marks_expired_membership(
    test_transaction_manager: TransactionManager,
    test_user: User,
    user_membership: UserMembership,
) -> None:
    async with test_transaction_manager:
        await test_transaction_manager.user_membership_repository.update(
            user_membership.id,
            expires_at=datetime.now(timezone.utc) - timedelta(days=1),
        )

    report = await _build_use_case(test_transaction_manager).execute(test_user)

    assert report.status == MembershipStatusEnum.EXPIRED


async def test_report_aggregates_available_membership_changes(
    test_transaction_manager: TransactionManager,
    test_user: User,
    purchasable_membership_type: MembershipType,
    user_membership: UserMembership,
) -> None:
    now = datetime.now(timezone.utc)
    previous_expiration = now + timedelta(days=30)
    new_expiration = now + timedelta(days=395)

    async with test_transaction_manager:
        membership_types, _ = await test_transaction_manager.membership_type_repository.list()
        target_type = next(item for item in membership_types if item.id != purchasable_membership_type.id)

        await test_transaction_manager.payment_repository.create(
            provider=PaymentProvider.STRIPE,
            amount=100,
            status=PaymentStatusEnum.SUCCEEDED,
            purpose=PaymentPurposeEnum.MEMBERSHIP_RENEWAL,
            user_id=test_user.id,
            provider_data={
                "user_membership_id": user_membership.id,
                "previous_expires_at": previous_expiration.isoformat(),
                "new_expires_at": new_expiration.isoformat(),
            },
        )
        await test_transaction_manager.payment_repository.create(
            provider=PaymentProvider.STRIPE,
            amount=100,
            status=PaymentStatusEnum.SUCCEEDED,
            purpose=PaymentPurposeEnum.MEMBERSHIP_TYPE_UPGRADE,
            user_id=test_user.id,
            provider_data={
                "user_membership_id": user_membership.id,
                "previous_membership_type_id": purchasable_membership_type.id,
                "target_membership_type_id": target_type.id,
            },
        )
        await test_transaction_manager.membership_downgrade_requests_repository.create(
            user_membership_id=user_membership.id,
            target_membership_type_id=target_type.id,
            reason_changing="Prefer another membership type",
            approved=True,
            pending=False,
        )

    report = await _build_use_case(test_transaction_manager).execute(test_user)

    event_types = [event.event_type for event in report.history]
    assert event_types.count(MembershipHistoryEventTypeEnum.RENEWED) == 1
    assert event_types.count(MembershipHistoryEventTypeEnum.TYPE_CHANGED) == 2

    renewal = next(event for event in report.history if event.event_type == MembershipHistoryEventTypeEnum.RENEWED)
    assert renewal.previous_valid_through == previous_expiration
    assert renewal.valid_through == new_expiration

    upgrade = next(
        event
        for event in report.history
        if event.event_type == MembershipHistoryEventTypeEnum.TYPE_CHANGED
        and event.previous_membership_type is not None
    )
    assert upgrade.previous_membership_type == purchasable_membership_type.name
    assert upgrade.membership_type == target_type.name
