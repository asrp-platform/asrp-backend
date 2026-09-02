from datetime import datetime, timedelta, timezone

import pytest
from faker import Faker
from httpx import AsyncClient

from app.domains.memberships.models import UserMembership
from app.domains.news.models import Webinar
from app.domains.shared.transaction_managers import TransactionManager
from tests.fixtures.auth import AuthHeaders


pytestmark = pytest.mark.anyio


async def test_get_webinars_as_guest(client: AsyncClient, webinar: Webinar) -> None:
    response = await client.get("/api/webinars")

    assert response.status_code == 200
    data = response.json()
    webinar_data = next(item for item in data["data"] if item["id"] == webinar.id)
    assert webinar_data["is_registered"] is False
    assert webinar_data["registration_link"] == webinar.registration_link
    assert webinar_data["bunny_video_id"] == webinar.bunny_video_id


async def test_live_public_webinar_join_link_is_available_to_guest(
    client: AsyncClient,
    webinar: Webinar,
    test_transaction_manager: TransactionManager,
) -> None:
    now = datetime.now(timezone.utc)
    async with test_transaction_manager:
        await test_transaction_manager.webinar_repository.update(
            webinar.id,
            starts_at=now - timedelta(minutes=5),
            ends_at=now + timedelta(hours=1),
        )

    response = await client.get("/api/webinars")

    assert response.status_code == 200
    webinar_data = next(item for item in response.json()["data"] if item["id"] == webinar.id)
    assert webinar_data["join_link"] == webinar.join_link


async def test_public_webinar_join_link_is_available_ten_minutes_before_start(
    client: AsyncClient,
    webinar: Webinar,
    test_transaction_manager: TransactionManager,
) -> None:
    now = datetime.now(timezone.utc)
    async with test_transaction_manager:
        await test_transaction_manager.webinar_repository.update(
            webinar.id,
            starts_at=now + timedelta(minutes=9),
            ends_at=now + timedelta(hours=2),
        )

    response = await client.get("/api/webinars")

    assert response.status_code == 200
    webinar_data = next(item for item in response.json()["data"] if item["id"] == webinar.id)
    assert webinar_data["join_link"] == webinar.join_link


async def test_public_webinar_join_link_is_hidden_before_join_window(
    client: AsyncClient,
    webinar: Webinar,
    test_transaction_manager: TransactionManager,
) -> None:
    now = datetime.now(timezone.utc)
    async with test_transaction_manager:
        await test_transaction_manager.webinar_repository.update(
            webinar.id,
            starts_at=now + timedelta(minutes=11),
            ends_at=now + timedelta(hours=2),
        )

    response = await client.get("/api/webinars")

    assert response.status_code == 200
    webinar_data = next(item for item in response.json()["data"] if item["id"] == webinar.id)
    assert "join_link" not in webinar_data


async def test_get_webinars_as_authenticated_user(
    client: AsyncClient,
    auth_headers: AuthHeaders,
    webinar: Webinar,
) -> None:
    response = await client.get("/api/webinars", headers=auth_headers)

    assert response.status_code == 200
    webinar_data = next(item for item in response.json()["data"] if item["id"] == webinar.id)
    assert webinar_data["is_registered"] is False


async def test_public_webinar_uses_external_registration(
    client: AsyncClient,
    auth_headers: AuthHeaders,
    webinar: Webinar,
) -> None:
    response = await client.post(
        f"/api/webinars/{webinar.slug}/registrations",
        headers=auth_headers,
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "Public webinars use external registration"


async def test_register_for_webinar_without_authentication(
    client: AsyncClient,
    webinar: Webinar,
) -> None:
    response = await client.post(f"/api/webinars/{webinar.slug}/registrations")

    assert response.status_code == 401


async def test_register_for_missing_webinar_returns_404(
    faker: Faker,
    client: AsyncClient,
    auth_headers: AuthHeaders,
) -> None:
    response = await client.post(
        f"/api/webinars/{faker.slug()}/registrations",
        headers=auth_headers,
    )

    assert response.status_code == 404


async def test_register_for_member_only_webinar_without_membership_returns_403(
    client: AsyncClient,
    auth_headers: AuthHeaders,
    member_only_webinar: Webinar,
) -> None:
    response = await client.post(
        f"/api/webinars/{member_only_webinar.slug}/registrations",
        headers=auth_headers,
    )

    assert response.status_code == 403


async def test_register_for_member_only_webinar_with_active_membership(
    client: AsyncClient,
    auth_headers: AuthHeaders,
    member_only_webinar: Webinar,
    user_membership: UserMembership,
) -> None:
    response = await client.post(
        f"/api/webinars/{member_only_webinar.slug}/registrations",
        headers=auth_headers,
    )

    assert response.status_code == 201


async def test_get_public_webinar_playback_requires_membership(
    client: AsyncClient,
    auth_headers: AuthHeaders,
    webinar: Webinar,
) -> None:
    response = await client.get(
        f"/api/webinars/{webinar.slug}/playback",
        headers=auth_headers,
    )

    assert response.status_code == 403


async def test_get_public_webinar_playback_with_active_membership(
    client: AsyncClient,
    auth_headers: AuthHeaders,
    webinar: Webinar,
    user_membership: UserMembership,
) -> None:
    response = await client.get(
        f"/api/webinars/{webinar.slug}/playback",
        headers=auth_headers,
    )

    assert response.status_code == 200


async def test_get_webinar_playback_without_authentication(
    client: AsyncClient,
    webinar: Webinar,
) -> None:
    response = await client.get(f"/api/webinars/{webinar.slug}/playback")

    assert response.status_code == 401


async def test_get_missing_webinar_playback_returns_404(
    faker: Faker,
    client: AsyncClient,
    auth_headers: AuthHeaders,
) -> None:
    response = await client.get(
        f"/api/webinars/{faker.slug()}/playback",
        headers=auth_headers,
    )

    assert response.status_code == 404


async def test_get_member_only_webinar_playback_without_membership_returns_403(
    client: AsyncClient,
    auth_headers: AuthHeaders,
    member_only_webinar: Webinar,
) -> None:
    response = await client.get(
        f"/api/webinars/{member_only_webinar.slug}/playback",
        headers=auth_headers,
    )

    assert response.status_code == 403
