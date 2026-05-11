from random import choice

import pytest
from faker import Faker
from sqlalchemy import select

from app.domains.memberships.models import (
    MembershipRequest,
    MembershipRequestStatusEnum,
    MembershipType,
    MembershipTypeEnum,
)
from app.domains.shared.transaction_managers import TransactionManager
from app.domains.users.models import User


@pytest.fixture(scope="function")
async def user_membership_request(
    test_user: User,
    test_transaction_manager: TransactionManager,
    user_membership_request_data,
) -> MembershipRequest:
    async with test_transaction_manager:
        membership_type = await test_transaction_manager.membership_type_repository.get_first_by_kwargs(
            type=user_membership_request_data["membership_type"],
        )

        user_membership = await test_transaction_manager.membership_requests_repository.create(
            user_id=test_user.id,
            membership_type_id=membership_type.id,
            **user_membership_request_data["membership"],
        )
        return user_membership


@pytest.fixture(scope="function")
def user_membership_request_data(faker: Faker):
    return {
        "membership": {
            "primary_affiliation": faker.text(max_nb_chars=50),
            "job_title": faker.text(max_nb_chars=50),
            "practice_setting": faker.text(max_nb_chars=50),
            "subspecialty": faker.text(max_nb_chars=50),
        },
        "membership_type": faker.random_element(
            [item.value for item in MembershipTypeEnum if item != MembershipTypeEnum.HONORARY]
        ),
        "feedback_additional_info": {
            "hear_about_asrp": faker.text(max_nb_chars=50),
            "tg_username": f"@{faker.pystr(min_chars=5, max_chars=32)}",
            "interest_description": faker.text(max_nb_chars=100),
        },
        "is_agrees_communications": False,
    }


@pytest.fixture(scope="function")
def membership_request_create_data(faker: Faker) -> dict:
    return {
        "membership": {
            "primary_affiliation": faker.company(),
            "job_title": faker.job(),
            "practice_setting": faker.word(),
            "subspecialty": faker.word(),
        },
        "membership_type": faker.random_element(
            [item for item in MembershipTypeEnum if item != MembershipTypeEnum.HONORARY]
        ),
        "feedback_additional_info": {
            "hear_about_asrp": faker.sentence(),
            "tg_username": f"@{faker.user_name()[:20]}",
            "interest_description": faker.text(max_nb_chars=200),
        },
        "is_agrees_communications": faker.boolean(),
    }


@pytest.fixture()
async def paid_membership_request(
    test_transaction_manager: TransactionManager,
    faker: Faker,
    test_user: User,
) -> MembershipRequest:
    async with test_transaction_manager:
        membership_types, _ = await test_transaction_manager.membership_type_repository.list(
            stmt=select(MembershipType).where(MembershipType.type != MembershipTypeEnum.HONORARY)
        )
        membership_type = choice(membership_types)

        return await test_transaction_manager.membership_requests_repository.create(
            status=MembershipRequestStatusEnum.PAID,
            primary_affiliation=faker.company(),
            job_title=faker.job(),
            practice_setting=faker.random_element(
                elements=[
                    "Hospital",
                    "Private practice",
                    "Academic medical center",
                    "Outpatient clinic",
                    "Research institute",
                ]
            ),
            subspecialty=faker.random_element(
                elements=[
                    "Cardiology",
                    "Neurology",
                    "Oncology",
                    "Pediatrics",
                    "Radiology",
                    "Surgery",
                    "Emergency medicine",
                ]
            ),
            user_id=test_user.id,
            membership_type_id=membership_type.id,
        )


@pytest.fixture()
async def _membership_request(
    test_transaction_manager: TransactionManager,
    faker: Faker,
    test_user: User,
) -> MembershipRequest:
    async with test_transaction_manager:
        membership_types, _ = await test_transaction_manager.membership_type_repository.list(
            stmt=select(MembershipType).where(MembershipType.type != MembershipTypeEnum.HONORARY)
        )
        membership_type = choice(membership_types)

        return await test_transaction_manager.membership_requests_repository.create(
            status=MembershipRequestStatusEnum.PAID,
            primary_affiliation=faker.company(),
            job_title=faker.job(),
            practice_setting=faker.random_element(
                elements=[
                    "Hospital",
                    "Private practice",
                    "Academic medical center",
                    "Outpatient clinic",
                    "Research institute",
                ]
            ),
            subspecialty=faker.random_element(
                elements=[
                    "Cardiology",
                    "Neurology",
                    "Oncology",
                    "Pediatrics",
                    "Radiology",
                    "Surgery",
                    "Emergency medicine",
                ]
            ),
            user_id=test_user.id,
            membership_type_id=membership_type.id,
        )
