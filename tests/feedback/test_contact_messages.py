import pytest
from faker import Faker
from httpx import AsyncClient

from app.domains.feedback.models import ContactMessage
from tests.fixtures.context import UserContext

pytestmark = pytest.mark.anyio


@pytest.mark.parametrize(
    "data_fixture",
    [
        "contact_message_data",
        "get_involved_message_data",
        "get_involved_committees_message_data",
    ],
)
async def test_create_directors_board_member(
    faker: Faker,
    client: AsyncClient,
    data_fixture: str,
    request: pytest.FixtureRequest,
) -> None:
    payload = request.getfixturevalue(data_fixture)

    response = await client.post(
        "/api/contact-messages",
        json=payload,
    )

    assert response.status_code == 201
    assert response.json()["name"] == payload["name"]


async def test_retrieve_contact_message(
    client: AsyncClient, admin_all_permissions_context: UserContext, contact_message_db: ContactMessage
) -> None:
    headers, _, _ = admin_all_permissions_context.auth

    response = await client.get(
        "/api/contact-messages",
        headers=headers,
    )
    response_data = response.json()["data"]

    assert response.status_code == 200
    assert contact_message_db.id in list(map(lambda m: m["id"], response_data))


async def test_retrieve_contact_message_not_authorized(
    client: AsyncClient,
) -> None:
    response = await client.get(
        "/api/contact-messages",
    )

    assert response.status_code == 401


async def test_retrieve_contact_message_by_user(
    client: AsyncClient,
    user_context: UserContext,
) -> None:
    headers, _, _ = user_context.auth

    response = await client.get(
        "/api/contact-messages",
        headers=headers,
    )

    assert response.status_code == 403


async def test_retrieve_contact_message_no_permissions(
    client: AsyncClient,
    admin_no_permissions_context: UserContext,
) -> None:
    headers, _, _ = admin_no_permissions_context.auth

    response = await client.get(
        "/api/contact-messages",
        headers=headers,
    )

    assert response.status_code == 403
