import pytest
from faker import Faker

from app.domains.memberships.infrastructure import MembershipUnitOfWork
from app.domains.memberships.models import MembershipTypeEnum, UserMembership
from app.domains.users.models import User


@pytest.fixture(scope="function")
async def membership(
    test_user: User,
    membership_uow: MembershipUnitOfWork,
    membership_data: dict,
) -> UserMembership:
    async with membership_uow:
        membership_type = await membership_uow.membership_type_repository.get_first_by_kwargs(
            type=membership_data["membership_type"],
        )

        membership = await membership_uow.membership_repository.create(
            user_id=test_user.id,
            membership_type_id=membership_type.id,
            **membership_data["membership"],
        )
        return membership


@pytest.fixture(scope="function")
def membership_data(faker: Faker):
    return {
        "membership": {
            "primary_affiliation": faker.text(max_nb_chars=50),
            "job_title": faker.text(max_nb_chars=50),
            "practice_setting": faker.text(max_nb_chars=50),
            "subspecialty": faker.text(max_nb_chars=50),
            "is_trained_in_us": faker.pybool(),
        },

        "membership_type": MembershipTypeEnum.TRAINEE.value,

        "feedback_additional_info": {
            "hear_about_asrp": faker.text(max_nb_chars=50),
            "tg_username": f"@{faker.pystr(min_chars=5, max_chars=32)}",
            "interest_description": faker.text(max_nb_chars=100),
        },

        "is_agrees_communications": True,
    }
