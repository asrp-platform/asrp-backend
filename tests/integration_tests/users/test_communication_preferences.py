import pytest
from httpx import AsyncClient

from app.domains.shared.deps import create_access_token
from app.domains.users.models import CommunicationPreferences, User
from tests.fixtures.auth import AuthHeaders, UserFactory

pytestmark = pytest.mark.anyio


async def test_create_user_communication_preferences_success(
    client: AsyncClient,
    test_user: User,
    auth_headers: AuthHeaders,
):
    response = await client.get(
        f"/api/users/{test_user.id}/communication-preferences",
        headers=auth_headers,
    )

    data = response.json()

    assert response.status_code == 200
    assert not data["newsletters"]
    assert not data["events_meetings"]
    assert not data["committees_leadership"]
    assert not data["volunteer_opportunities"]


async def test_get_user_communication_preferences(
    client: AsyncClient,
    test_user: User,
    auth_headers: AuthHeaders,
    communication_preferences: CommunicationPreferences,
):
    response = await client.get(
        f"/api/users/{test_user.id}/communication-preferences",
        headers=auth_headers,
    )

    data = response.json()

    assert response.status_code == 200
    assert data["newsletters"] == communication_preferences.newsletters
    assert data["events_meetings"] == communication_preferences.events_meetings
    assert data["committees_leadership"] == communication_preferences.committees_leadership
    assert data["volunteer_opportunities"] == communication_preferences.volunteer_opportunities


async def test_get_user_communication_preferences_not_found(
    client: AsyncClient,
    auth_headers: AuthHeaders,
):
    response = await client.get(
        "/api/users/999999/communication-preferences",
        headers=auth_headers,
    )

    data = response.json()

    assert response.status_code == 404
    assert "detail" in data


async def test_update_user_communication_preferences_success(
    client: AsyncClient,
    test_user: User,
    auth_headers: AuthHeaders,
    communication_preferences: CommunicationPreferences,
):
    payload = {
        "newsletters": False,
        "events_meetings": True,
    }

    response = await client.patch(
        f"/api/users/{test_user.id}/communication-preferences",
        headers=auth_headers,
        json=payload,
    )

    data = response.json()

    assert response.status_code == 200
    assert data["newsletters"] is False
    assert data["events_meetings"] is True
    assert data["committees_leadership"] == communication_preferences.committees_leadership
    assert data["volunteer_opportunities"] == communication_preferences.volunteer_opportunities


async def test_update_user_communication_preferences_partial_update_success(
    client: AsyncClient,
    test_user: User,
    auth_headers: AuthHeaders,
    communication_preferences: CommunicationPreferences,
):
    old_events_meetings = communication_preferences.events_meetings
    old_committees_leadership = communication_preferences.committees_leadership
    old_volunteer_opportunities = communication_preferences.volunteer_opportunities

    payload = {
        "newsletters": False,
    }

    response = await client.patch(
        f"/api/users/{test_user.id}/communication-preferences",
        headers=auth_headers,
        json=payload,
    )

    data = response.json()

    assert response.status_code == 200
    assert data["newsletters"] is False
    assert data["events_meetings"] == old_events_meetings
    assert data["committees_leadership"] == old_committees_leadership
    assert data["volunteer_opportunities"] == old_volunteer_opportunities


async def test_update_user_communication_preferences_not_found(
    client: AsyncClient,
    auth_headers: AuthHeaders,
):
    payload = {
        "newsletters": True,
    }

    response = await client.patch(
        "/api/users/999999/communication-preferences",
        headers=auth_headers,
        json=payload,
    )

    data = response.json()

    assert response.status_code == 404
    assert "detail" in data


async def test_update_user_communication_preferences_forbid_extra_fields(
    client: AsyncClient,
    test_user: User,
    auth_headers: AuthHeaders,
):
    payload = {
        "newsletters": True,
        "unknown_field": "test",
    }

    response = await client.patch(
        f"/api/users/{test_user.id}/communication-preferences",
        headers=auth_headers,
        json=payload,
    )

    assert response.status_code == 422


async def test_update_user_communication_preferences_forbidden_for_another_user(
    client: AsyncClient,
    test_user: User,
    user_factory: UserFactory,
):
    another_user = await user_factory()
    access_token = create_access_token({"email": another_user.email})

    payload = {
        "newsletters": True,
    }

    response = await client.patch(
        f"/api/users/{test_user.id}/communication-preferences",
        headers={"Authorization": f"Bearer {access_token}"},
        json=payload,
    )

    data = response.json()

    assert response.status_code == 403
    assert "detail" in data
