from datetime import datetime, timedelta

import pytest
from faker import Faker
from fastapi.encoders import jsonable_encoder
from httpx import AsyncClient

from app.domains.news.models import Webinar
from tests.fixtures.auth import AuthHeaders


pytestmark = pytest.mark.anyio


async def test_get_webinars_by_admin(
    client: AsyncClient,
    admin_auth_headers: AuthHeaders,
    webinar: Webinar,
) -> None:
    response = await client.get("/api/admin/webinars", headers=admin_auth_headers)

    assert response.status_code == 200
    assert any(item["id"] == webinar.id for item in response.json()["data"])


async def test_get_webinars_without_authentication_returns_401(client: AsyncClient) -> None:
    response = await client.get("/api/admin/webinars")

    assert response.status_code == 401


async def test_get_webinars_by_user_returns_403(
    client: AsyncClient,
    auth_headers: AuthHeaders,
) -> None:
    response = await client.get("/api/admin/webinars", headers=auth_headers)

    assert response.status_code == 403


async def test_create_webinar_by_admin(
    client: AsyncClient,
    admin_auth_headers: AuthHeaders,
    webinar_data: dict,
) -> None:
    response = await client.post(
        "/api/admin/webinars",
        headers=admin_auth_headers,
        json=jsonable_encoder(webinar_data),
    )

    assert response.status_code == 200
    assert response.json()["title"] == webinar_data["title"]


async def test_create_webinars_with_same_title(
    client: AsyncClient,
    admin_auth_headers: AuthHeaders,
    webinar_data: dict,
) -> None:
    first_response = await client.post(
        "/api/admin/webinars",
        headers=admin_auth_headers,
        json=jsonable_encoder(webinar_data),
    )
    second_response = await client.post(
        "/api/admin/webinars",
        headers=admin_auth_headers,
        json=jsonable_encoder(webinar_data),
    )

    assert first_response.status_code == 200
    assert second_response.status_code == 200
    assert first_response.json()["slug"] != second_response.json()["slug"]


async def test_update_webinar_by_admin(
    faker: Faker,
    client: AsyncClient,
    admin_auth_headers: AuthHeaders,
    webinar: Webinar,
) -> None:
    update_data = {"title": faker.sentence(nb_words=4)}
    response = await client.patch(
        f"/api/admin/webinars/{webinar.id}",
        headers=admin_auth_headers,
        json=update_data,
    )

    assert response.status_code == 200
    assert response.json()["title"] == update_data["title"]


async def test_update_webinar_starts_at_updates_ends_at(
    faker: Faker,
    client: AsyncClient,
    admin_auth_headers: AuthHeaders,
    webinar: Webinar,
) -> None:
    starts_at = faker.future_datetime(tzinfo=webinar.starts_at.tzinfo)

    response = await client.patch(
        f"/api/admin/webinars/{webinar.id}",
        headers=admin_auth_headers,
        json=jsonable_encoder({"starts_at": starts_at}),
    )

    assert response.status_code == 200
    ends_at = datetime.fromisoformat(response.json()["ends_at"].replace("Z", "+00:00"))
    assert ends_at == starts_at + timedelta(hours=2)


async def test_delete_webinar_by_admin(
    client: AsyncClient,
    admin_auth_headers: AuthHeaders,
    webinar: Webinar,
) -> None:
    response = await client.delete(
        f"/api/admin/webinars/{webinar.id}",
        headers=admin_auth_headers,
    )

    assert response.status_code == 200


@pytest.mark.parametrize("method", ["patch", "delete"])
async def test_change_missing_webinar_returns_404(
    method: str,
    faker: Faker,
    client: AsyncClient,
    admin_auth_headers: AuthHeaders,
) -> None:
    request = getattr(client, method)
    kwargs = {"json": {"title": faker.sentence(nb_words=4)}} if method == "patch" else {}

    response = await request(
        "/api/admin/webinars/999999999",
        headers=admin_auth_headers,
        **kwargs,
    )

    assert response.status_code == 404
