from datetime import datetime, timedelta, timezone

import pytest
from faker import Faker

from app.domains.memberships.models import (
    MembershipDowngradeRequest,
    MembershipRequest,
    MembershipRequestStatusEnum,
    UserMembership,
)
from app.domains.shared.transaction_managers import TransactionManager
from app.domains.users.models import User


@pytest.fixture(scope="function")
async def user_membership_request(
    test_transaction_manager: TransactionManager,
    test_user: User,
    purchasable_membership_type_id: int,
    membership_request_fields: dict,
) -> MembershipRequest:
    async with test_transaction_manager:
        return await test_transaction_manager.membership_requests_repository.create(
            user_id=test_user.id,
            membership_type_id=purchasable_membership_type_id,
            **membership_request_fields,
        )


@pytest.fixture()
async def payment_pending_membership_request(user_membership_request: MembershipRequest) -> MembershipRequest:
    return user_membership_request


@pytest.fixture()
async def paid_membership_request(
    test_transaction_manager: TransactionManager,
    test_user: User,
    purchasable_membership_type_id: int,
    membership_request_fields: dict,
) -> MembershipRequest:
    async with test_transaction_manager:
        return await test_transaction_manager.membership_requests_repository.create(
            user_id=test_user.id,
            membership_type_id=purchasable_membership_type_id,
            status=MembershipRequestStatusEnum.PAID,
            **membership_request_fields,
        )


@pytest.fixture()
async def rejected_membership_request(
    test_transaction_manager: TransactionManager,
    test_user: User,
    admin_user: User,
    purchasable_membership_type_id: int,
    membership_request_fields: dict,
    faker: Faker,
) -> MembershipRequest:
    async with test_transaction_manager:
        return await test_transaction_manager.membership_requests_repository.create(
            user_id=test_user.id,
            membership_type_id=purchasable_membership_type_id,
            status=MembershipRequestStatusEnum.REJECTED,
            reviewed_at=datetime.now(timezone.utc),
            admin_comment=faker.sentence(),
            reviewer_id=admin_user.id,
            **membership_request_fields,
        )


@pytest.fixture()
async def user_membership(
    test_transaction_manager: TransactionManager,
    paid_membership_request: MembershipRequest,
) -> UserMembership:
    return await test_transaction_manager.user_membership_repository.create(
        user_id=paid_membership_request.user_id,
        membership_request_id=paid_membership_request.id,
        membership_type_id=paid_membership_request.membership_type_id,
        expires_at=datetime.now(timezone.utc) + timedelta(days=30),
    )


@pytest.fixture()
async def membership_downgrade_request(
    test_transaction_manager: TransactionManager, user_membership: UserMembership
) -> MembershipDowngradeRequest:
    async with test_transaction_manager:
        membership_types, _ = await test_transaction_manager.membership_type_repository.list()
        target_membership_type = next(
            membership_type
            for membership_type in membership_types
            if membership_type.id != user_membership.membership_type_id
        )

        await test_transaction_manager.flush()

        downgrade_request = await test_transaction_manager.membership_downgrade_requests_repository.create(
            user_membership_id=user_membership.id,
            target_membership_type_id=target_membership_type.id,
            reason_changing="I want to switch to a cheaper membership type",
        )

    return downgrade_request
