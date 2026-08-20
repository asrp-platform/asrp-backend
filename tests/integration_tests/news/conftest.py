from datetime import timezone
from unittest.mock import AsyncMock

import pytest
from faker import Faker

from app.domains.news.cache import NewsCache
from app.domains.news.models import News, Webinar
from app.domains.shared.transaction_managers import TransactionManager
from app.domains.users.models import User


@pytest.fixture(autouse=True)
def news_cache(client):
    from app.main import app

    cache = AsyncMock(spec=NewsCache)
    cache.get_first_page_from_cache.return_value = None
    app.dependency_overrides[NewsCache] = lambda: cache
    yield cache
    app.dependency_overrides.pop(NewsCache, None)


@pytest.fixture()
def webinar_data(faker: Faker) -> dict:
    return {
        "title": faker.sentence(nb_words=4),
        "description": faker.paragraph(),
        "learning_objectives": faker.sentences(nb=2),
        "speaker_name": faker.name(),
        "speaker_description": faker.sentence(),
        "join_link": faker.url(),
        "registration_link": faker.url(),
        "bunny_video_id": faker.uuid4(),
        "starts_at": faker.future_datetime(tzinfo=timezone.utc),
        "location": faker.city(),
        "member_only": False,
    }


@pytest.fixture()
def webinar_create_data(webinar_data: dict) -> dict:
    create_data = webinar_data.copy()
    create_data.pop("bunny_video_id")
    create_data.update(timezone="America/Chicago")
    return create_data


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


@pytest.fixture()
def news_create_data(faker: Faker) -> dict:
    return {
        "title": faker.sentence(nb_words=4),
        "cover_key": None,
        "body": {"content": faker.paragraph()},
        "when": None,
        "where": None,
        "is_published": True,
    }


@pytest.fixture()
async def news(
    faker: Faker,
    news_create_data: dict,
    admin_user: User,
    test_transaction_manager: TransactionManager,
) -> News:
    async with test_transaction_manager:
        return await test_transaction_manager.news_repository.create(
            **news_create_data,
            author_id=admin_user.id,
            slug=faker.unique.slug(),
        )
