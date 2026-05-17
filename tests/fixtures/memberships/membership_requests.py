from datetime import datetime, timezone

import pytest
from faker import Faker

from app.domains.memberships.models import MembershipRequest, MembershipRequestStatusEnum
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
