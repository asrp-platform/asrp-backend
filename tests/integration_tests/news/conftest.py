from datetime import timezone

import pytest
from faker import Faker

from app.domains.news.models import Webinar
from app.domains.shared.transaction_managers import TransactionManager


@pytest.fixture()
def webinar_data(faker: Faker) -> dict:
    return {
        "title": faker.sentence(nb_words=4),
        "description": faker.paragraph(),
        "learning_objectives": faker.sentences(nb=2),
        "speaker_name": faker.name(),
        "speaker_description": faker.sentence(),
        "registration_link": faker.url(),
        "join_link": faker.url(),
        "starts_at": faker.future_datetime(tzinfo=timezone.utc),
        "location": faker.city(),
        "member_only": False,
    }


@pytest.fixture()
async def webinar(
    faker: Faker,
    webinar_data: dict,
    test_transaction_manager: TransactionManager,
) -> Webinar:
    async with test_transaction_manager:
        return await test_transaction_manager.webinar_repository.create(
            **webinar_data,
            slug=faker.unique.slug(),
        )


@pytest.fixture()
async def member_only_webinar(
    webinar: Webinar,
    test_transaction_manager: TransactionManager,
) -> Webinar:
    async with test_transaction_manager:
        return await test_transaction_manager.webinar_repository.update(
            webinar.id,
            member_only=True,
        )
