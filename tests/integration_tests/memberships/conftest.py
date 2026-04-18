import pytest
from faker import Faker

from app.domains.memberships.models import MembershipRequest, MembershipTypeEnum
from app.domains.shared.transaction_managers import TransactionManager
from app.domains.users.models import User


@pytest.fixture(scope="function")
async def user_membership(
    test_user: User,
    test_transaction_manager: TransactionManager,
    user_membership_data: dict,
) -> MembershipRequest:
    async with test_transaction_manager:
        membership_type = await test_transaction_manager.membership_type_repository.get_first_by_kwargs(
            type=user_membership_data["membership_type"],
        )

        user_membership = await test_transaction_manager.membership_requests_repository.create(
            user_id=test_user.id,
            membership_type_id=membership_type.id,
            **user_membership_data["membership"],
        )
        return user_membership


@pytest.fixture(scope="function")
def user_membership_data(faker: Faker):
    return {
        "membership": {
            "primary_affiliation": faker.text(max_nb_chars=50),
            "job_title": faker.text(max_nb_chars=50),
            "practice_setting": faker.text(max_nb_chars=50),
            "subspecialty": faker.text(max_nb_chars=50),
        },
        "membership_type": MembershipTypeEnum.TRAINEE.value,
        "feedback_additional_info": {
            "hear_about_asrp": faker.text(max_nb_chars=50),
            "tg_username": f"@{faker.pystr(min_chars=5, max_chars=32)}",
            "interest_description": faker.text(max_nb_chars=100),
        },
        "is_agrees_communications": False,
    }
