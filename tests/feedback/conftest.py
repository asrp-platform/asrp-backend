import random

import pytest
from faker import Faker

from app.domains.feedback.models import ContactMessage, ContactMessageTypeEnum
from app.domains.shared.transaction_managers import TransactionManager


@pytest.fixture(scope="function")
def contact_message_data(faker: Faker) -> dict:
    return {
        "name": faker.name(),
        "email": faker.email(),
        "type": ContactMessageTypeEnum.CONTACT.value,
        "message_content": {
            "subject": (random.choice(CONTACT_SUBJECTS) if random.choice([True, False]) else None),
            "contact_message": (faker.paragraph(nb_sentences=3) if random.choice([True, False]) else None),
        },
    }


ROLE_AFFILIATIONS = [
    "Pathology Resident",
    "Pathology Fellow",
    "Attending Pathologist",
    "Research Scientist",
    "Medical Student",
]


CONTACT_SUBJECTS = [
    "General inquiry",
    "Membership question",
    "Website feedback",
    "Technical issue",
    "Collaboration request",
]


@pytest.fixture(scope="function")
def get_involved_message_data(faker: Faker) -> dict:
    return {
        "name": faker.name(),
        "email": faker.email(),
        "type": ContactMessageTypeEnum.GET_INVOLVED.value,
        "message_content": {
            "role_affiliation": (random.choice(ROLE_AFFILIATIONS) if random.choice([True, False]) else None),
            "get_involved_message": (faker.paragraph(nb_sentences=3) if random.choice([True, False]) else None),
        },
    }


AREAS_POOL = [
    "Hematopathology",
    "Surgical Pathology",
    "Cytopathology",
    "Molecular Pathology",
    "Digital Pathology",
    "Transfusion Medicine",
    "Clinical Pathology",
    "Forensic Pathology",
]

ROLES_POOL = [
    "Pathology Resident",
    "Pathology Fellow",
    "Attending Pathologist",
    "Research Fellow",
    "Medical Student",
    None,
]


@pytest.fixture(scope="function")
def get_involved_committees_message_data(faker: Faker) -> dict:
    return {
        "name": faker.name(),
        "email": faker.email(),
        "type": ContactMessageTypeEnum.GET_INVOLVED_COMMITTEES.value,
        "message_content": {
            "current_role": random.choice(ROLES_POOL),
            "institution_location": (
                f"{faker.city()}, {faker.state_abbr()}, USA" if random.choice([True, False]) else None
            ),
            "areas": random.sample(AREAS_POOL, k=random.randint(0, min(3, len(AREAS_POOL)))),
            "ideas": (faker.paragraph(nb_sentences=2) if random.choice([True, False]) else None),
            "future_committee_working": faker.boolean(),
            "future_leadership_positions": faker.boolean(),
            "receive_updates": faker.boolean(),
        },
    }


@pytest.fixture(scope="function")
async def contact_message_db(
    test_transaction_manager: TransactionManager, get_involved_committees_message_data: dict
) -> ContactMessage:
    return await test_transaction_manager.contact_message_repository.create(**get_involved_committees_message_data)
