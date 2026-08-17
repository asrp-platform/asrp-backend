from unittest.mock import AsyncMock

import pytest
from faker import Faker
from httpx import AsyncClient

from app.domains.news.models import News
from app.domains.shared.transaction_managers import TransactionManager
from app.domains.users.models import User


pytestmark = pytest.mark.anyio


async def test_public_news_detail_contains_presigned_cover_url(
    client: AsyncClient,
    news: News,
    file_storage,
    monkeypatch: pytest.MonkeyPatch,
    test_transaction_manager: TransactionManager,
) -> None:
    cover_key = "news/cover.jpg"
    cover_url = "https://storage.example/news/cover.jpg?signature=test"
    get_file_url = AsyncMock(return_value=cover_url)
    monkeypatch.setattr(file_storage, "get_file_url", get_file_url)

    async with test_transaction_manager:
        news = await test_transaction_manager.news_repository.update(news.id, cover_key=cover_key)

    response = await client.get(f"/api/news/{news.slug}")

    assert response.status_code == 200
    assert response.json()["cover_key"] == cover_key
    assert response.json()["cover_url"] == cover_url
    get_file_url.assert_awaited_once_with(cover_key)


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


async def test_public_news_detail_returns_published_news(
    client: AsyncClient,
    news: News,
) -> None:
    response = await client.get(f"/api/news/{news.slug}")

    assert response.status_code == 200
    assert response.json()["id"] == news.id
    assert response.json()["slug"] == news.slug


async def test_public_news_detail_hides_draft(
    faker: Faker,
    client: AsyncClient,
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

    response = await client.get(f"/api/news/{draft.slug}")

    assert response.status_code == 404
