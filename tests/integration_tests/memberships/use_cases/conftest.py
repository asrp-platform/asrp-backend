import pytest
from faker import Faker

from app.domains.memberships.models import MembershipTypeEnum


@pytest.fixture()
def membership_request_create_data(faker: Faker) -> dict:
    return {
        "membership": {
            "primary_affiliation": faker.company(),
            "job_title": faker.job(),
            "practice_setting": faker.word(),
            "subspecialty": faker.word(),
        },
        "membership_type": faker.random_element([item for item in MembershipTypeEnum]),
        "feedback_additional_info": {
            "hear_about_asrp": faker.sentence(),
            "tg_username": f"@{faker.user_name()[:20]}",
            "interest_description": faker.text(max_nb_chars=200),
        },
        "is_agrees_communications": faker.boolean(),
    }
