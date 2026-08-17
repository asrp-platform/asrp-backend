import pytest
from faker import Faker
from httpx import AsyncClient

from app.domains.news.models import News
from app.domains.shared.transaction_managers import TransactionManager
from app.domains.users.models import User


pytestmark = pytest.mark.anyio


async def test_public_news_returns_only_published_news(
    faker: Faker,
    client: AsyncClient,
    news: News,
    admin_user: User,
    news_create_data: dict,
    test_transaction_manager: TransactionManager,
) -> None:
    async with test_transaction_manager:
        draft = await test_transaction_manager.news_repository.create(
            **(news_create_data | {"title": faker.sentence(), "is_published": False}),
            author_id=admin_user.id,
            slug=faker.unique.slug(),
        )

    response = await client.get("/api/news")

    assert response.status_code == 200
    returned_ids = {item["id"] for item in response.json()["data"]}
    assert news.id in returned_ids
    assert draft.id not in returned_ids
    assert all(item["is_published"] for item in response.json()["data"])
