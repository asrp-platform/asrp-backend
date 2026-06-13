import pytest
from faker import Faker

from app.domains.feedback.constants import HEAR_ABOUT_ASRP_OPTIONS
from app.domains.memberships.models import MembershipTypeEnum


@pytest.fixture()
def membership_request_fields(faker: Faker) -> dict:
    return {
        "primary_affiliation": faker.company(),
        "job_title": faker.job(),
        "practice_setting": faker.word(),
        "subspecialty": faker.word(),
    }


@pytest.fixture()
async def membership_reapply_payload(
    faker: Faker,
    purchasable_membership_type_id: int,
) -> dict:
    return {
        "primary_affiliation": faker.company(),
        "job_title": faker.job(),
        "practice_setting": faker.word(),
        "subspecialty": faker.word(),
        "membership_type_id": purchasable_membership_type_id,
    }


@pytest.fixture()
def feedback_additional_info_data(faker: Faker) -> dict:
    return {
        "hear_about_asrp": faker.random_element(HEAR_ABOUT_ASRP_OPTIONS),
        "tg_username": f"@{faker.user_name()[:20]}",
        "interest_description": faker.text(max_nb_chars=200),
    }


@pytest.fixture(scope="function")
def user_membership_request_data(
    membership_request_fields: dict,
    feedback_additional_info_data: dict,
    purchasable_membership_type_value: str,
) -> dict:
    return {
        "membership": membership_request_fields,
        "membership_type": purchasable_membership_type_value,
        "feedback_additional_info": feedback_additional_info_data,
        "is_agrees_communications": False,
    }


@pytest.fixture(scope="function")
def honorary_user_membership_request_data(
    user_membership_request_data: dict,
    honorary_membership_type_value: str,
) -> dict:
    return {
        **user_membership_request_data,
        "membership_type": honorary_membership_type_value,
    }


@pytest.fixture(scope="function")
def membership_request_create_data(
    membership_request_fields: dict,
    feedback_additional_info_data: dict,
    purchasable_membership_type_enum: MembershipTypeEnum,
    faker: Faker,
) -> dict:
    return {
        "membership": membership_request_fields,
        "membership_type": purchasable_membership_type_enum,
        "feedback_additional_info": feedback_additional_info_data,
        "is_agrees_communications": faker.boolean(),
    }
