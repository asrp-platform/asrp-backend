import pytest
from faker import Faker
from httpx import AsyncClient

from app.domains.news.models import News
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


async def test_admin_create_news(
    client: AsyncClient,
    admin_auth_headers: AuthHeaders,
    admin_all_permissions,
    news_create_data: dict,
) -> None:
    response = await client.post("/api/admin/news", headers=admin_auth_headers, json=news_create_data)

    assert response.status_code == 201
    assert response.json()["title"] == news_create_data["title"]


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
