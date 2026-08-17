from unittest.mock import AsyncMock

import pytest
from faker import Faker
from httpx import AsyncClient

from app.domains.news.models import News
from app.domains.shared.transaction_managers import TransactionManager
from tests.fixtures.auth import AuthHeaders


pytestmark = pytest.mark.anyio


async def test_admin_get_news_list(
    client: AsyncClient,
    admin_auth_headers: AuthHeaders,
    admin_all_permissions,
    news: News,
) -> None:
    response = await client.get("/api/admin/news", headers=admin_auth_headers)

    assert response.status_code == 200
    assert response.json()["count"] == 1
    assert response.json()["data"][0]["id"] == news.id


async def test_admin_news_list_supports_filters_sorting_and_pagination(
    client: AsyncClient,
    admin_auth_headers: AuthHeaders,
    admin_all_permissions,
    news: News,
    news_create_data: dict,
    test_transaction_manager: TransactionManager,
) -> None:
    async with test_transaction_manager:
        matching_news = await test_transaction_manager.news_repository.create(
            **(
                news_create_data
                | {
                    "title": "Administration release update",
                    "where": "Chicago",
                    "is_published": False,
                    "author_id": news.author_id,
                }
            )
        )
        await test_transaction_manager.flush()
        matching_news_id = matching_news.id

    response = await client.get(
        "/api/admin/news",
        headers=admin_auth_headers,
        params={
            "title__startswith": "Administration",
            "where__startswith": "Chic",
            "is_published": False,
            "ordering": "-id",
            "page": 1,
            "page_size": 1,
        },
    )

    assert response.status_code == 200
    assert response.json()["count"] == 1
    assert response.json()["page"] == 1
    assert response.json()["page_size"] == 1
    assert response.json()["data"][0]["id"] == matching_news_id


async def test_admin_create_news(
    client: AsyncClient,
    admin_auth_headers: AuthHeaders,
    admin_all_permissions,
    news_create_data: dict,
) -> None:
    response = await client.post("/api/admin/news", headers=admin_auth_headers, json=news_create_data)

    assert response.status_code == 201
    assert response.json()["title"] == news_create_data["title"]


async def test_admin_create_news_stores_content_image_key_and_returns_fresh_url(
    client: AsyncClient,
    admin_auth_headers: AuthHeaders,
    admin_all_permissions,
    news_create_data: dict,
    file_storage,
    monkeypatch: pytest.MonkeyPatch,
    test_transaction_manager: TransactionManager,
) -> None:
    object_key = "news/content-image.jpg"
    uploaded_url = "https://storage.example/news/content-image.jpg?old-signature"
    fresh_url = "https://storage.example/news/content-image.jpg?fresh-signature"
    get_file_url = AsyncMock(return_value=fresh_url)
    monkeypatch.setattr(file_storage, "get_file_url", get_file_url)
    body = {
        "type": "doc",
        "content": [
            {
                "type": "image",
                "attrs": {"src": uploaded_url, "objectKey": object_key, "alt": "Content image"},
            }
        ],
    }

    response = await client.post(
        "/api/admin/news",
        headers=admin_auth_headers,
        json=news_create_data | {"body": body},
    )

    assert response.status_code == 201
    response_attrs = response.json()["body"]["content"][0]["attrs"]
    assert response_attrs["src"] == fresh_url
    assert response_attrs["objectKey"] == object_key

    async with test_transaction_manager:
        stored_news = await test_transaction_manager.news_repository.get_first_by_kwargs(id=response.json()["id"])

    stored_attrs = stored_news.body["content"][0]["attrs"]
    assert stored_attrs["src"] == object_key
    assert stored_attrs["objectKey"] == object_key


async def test_admin_get_update_and_delete_news(
    faker: Faker,
    client: AsyncClient,
    admin_auth_headers: AuthHeaders,
    admin_all_permissions,
    news: News,
) -> None:
    detail_response = await client.get(f"/api/admin/news/{news.id}", headers=admin_auth_headers)
    assert detail_response.status_code == 200

    title = faker.sentence(nb_words=3)
    update_response = await client.patch(
        f"/api/admin/news/{news.id}",
        headers=admin_auth_headers,
        json={"title": title},
    )
    assert update_response.status_code == 200
    assert update_response.json()["title"] == title

    delete_response = await client.delete(f"/api/admin/news/{news.id}", headers=admin_auth_headers)
    assert delete_response.status_code == 204


@pytest.mark.parametrize("method", ["get", "patch", "delete"])
async def test_admin_news_missing_returns_404(
    method: str,
    client: AsyncClient,
    admin_auth_headers: AuthHeaders,
    admin_all_permissions,
) -> None:
    request = getattr(client, method)
    kwargs = {"json": {"title": "Updated title"}} if method == "patch" else {}
    response = await request("/api/admin/news/999999999", headers=admin_auth_headers, **kwargs)

    assert response.status_code == 404


async def test_admin_news_without_permission_returns_403(
    client: AsyncClient,
    admin_auth_headers: AuthHeaders,
) -> None:
    response = await client.get("/api/admin/news", headers=admin_auth_headers)

    assert response.status_code == 403


async def test_admin_news_mutations_without_permissions_return_403(
    client: AsyncClient,
    admin_auth_headers: AuthHeaders,
    news: News,
    news_create_data: dict,
) -> None:
    responses = [
        await client.post("/api/admin/news", headers=admin_auth_headers, json=news_create_data),
        await client.patch(
            f"/api/admin/news/{news.id}",
            headers=admin_auth_headers,
            json={"title": "Forbidden update"},
        ),
        await client.delete(f"/api/admin/news/{news.id}", headers=admin_auth_headers),
        await client.post(
            "/api/admin/news/images",
            headers=admin_auth_headers,
            files={"file": ("image.png", b"image", "image/png")},
        ),
    ]

    assert [response.status_code for response in responses] == [403, 403, 403, 403]


async def test_admin_update_news_removes_replaced_images(
    client: AsyncClient,
    admin_auth_headers: AuthHeaders,
    admin_all_permissions,
    news: News,
    file_storage,
    monkeypatch: pytest.MonkeyPatch,
    test_transaction_manager: TransactionManager,
) -> None:
    old_cover_key = "news/old-cover.jpg"
    old_content_key = "news/old-content.jpg"
    old_body = {
        "type": "doc",
        "content": [
            {"type": "image", "attrs": {"src": old_content_key, "objectKey": old_content_key}},
        ],
    }
    async with test_transaction_manager:
        await test_transaction_manager.news_repository.update(
            news.id,
            cover_key=old_cover_key,
            body=old_body,
        )

    delete_file = AsyncMock()
    monkeypatch.setattr(file_storage, "delete_file", delete_file)

    response = await client.patch(
        f"/api/admin/news/{news.id}",
        headers=admin_auth_headers,
        json={"cover_key": None, "body": {"type": "doc", "content": [{"type": "paragraph"}]}},
    )

    assert response.status_code == 200
    assert {call.args[0] for call in delete_file.await_args_list} == {old_cover_key, old_content_key}


async def test_admin_delete_news_removes_its_images(
    client: AsyncClient,
    admin_auth_headers: AuthHeaders,
    admin_all_permissions,
    news: News,
    file_storage,
    monkeypatch: pytest.MonkeyPatch,
    test_transaction_manager: TransactionManager,
) -> None:
    cover_key = "news/deleted-cover.jpg"
    content_key = "news/deleted-content.jpg"
    async with test_transaction_manager:
        await test_transaction_manager.news_repository.update(
            news.id,
            cover_key=cover_key,
            body={
                "type": "doc",
                "content": [{"type": "image", "attrs": {"objectKey": content_key, "src": content_key}}],
            },
        )

    delete_file = AsyncMock()
    monkeypatch.setattr(file_storage, "delete_file", delete_file)

    response = await client.delete(f"/api/admin/news/{news.id}", headers=admin_auth_headers)

    assert response.status_code == 204
    assert {call.args[0] for call in delete_file.await_args_list} == {cover_key, content_key}
