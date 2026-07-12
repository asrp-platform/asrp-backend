from unittest.mock import AsyncMock, patch

import pytest
from faker import Faker
from httpx import AsyncClient

from app.domains.emails.email_queue import EmailQueue
from app.domains.feedback.models import ContactMessage
from app.domains.shared.transaction_managers import TransactionManager
from tests.fixtures.auth import AuthHeaders


pytestmark = pytest.mark.anyio


@pytest.mark.parametrize(
    "data_fixture",
    [
        "contact_message_data",
        "get_involved_message_data",
        "get_involved_committees_message_data",
        "donation_sponsorship_message_data",
    ],
)
async def test_create_contact(
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
    client: AsyncClient,
    contact_message_db: ContactMessage,
    admin_auth_headers: AuthHeaders,
    admin_all_permissions,
) -> None:
    response = await client.get(
        "/api/admin/contact-messages",
        headers=admin_auth_headers,
    )
    response_data = response.json()["data"]

    assert response.status_code == 200
    assert contact_message_db.id in list(map(lambda m: m["id"], response_data))


async def test_retrieve_contact_message_not_authorized(
    client: AsyncClient,
) -> None:
    response = await client.get(
        "/api/admin/contact-messages",
    )

    assert response.status_code == 401


async def test_retrieve_contact_message_by_user(client: AsyncClient, auth_headers: AuthHeaders) -> None:
    response = await client.get(
        "/api/admin/contact-messages",
        headers=auth_headers,
    )

    assert response.status_code == 403


async def test_retrieve_contact_message_no_permissions(
    client: AsyncClient,
    admin_auth_headers: AuthHeaders,
) -> None:
    response = await client.get(
        "/api/admin/contact-messages",
        headers=admin_auth_headers,
    )

    assert response.status_code == 403


async def test_answer_contact_message_queues_email_and_marks_answered(
    client: AsyncClient,
    contact_message_db: ContactMessage,
    admin_auth_headers: AuthHeaders,
    admin_all_permissions,
    test_transaction_manager: TransactionManager,
) -> None:
    with patch.object(EmailQueue, "send_email", new_callable=AsyncMock) as mock_send_email:
        response = await client.post(
            f"/api/admin/contact-messages/{contact_message_db.id}/answers",
            json={
                "subject": "Reply from ASRP",
                "answer_message": "Thank you for contacting ASRP. We will be happy to help.",
            },
            headers=admin_auth_headers,
        )

    async with test_transaction_manager:
        updated_message = await test_transaction_manager.contact_message_repository.get_first_by_kwargs(
            id=contact_message_db.id
        )

    assert response.status_code == 201
    assert updated_message is not None
    assert updated_message.answered is True
    mock_send_email.assert_awaited_once_with(
        to=contact_message_db.email,
        subject="Reply from ASRP",
        body="Thank you for contacting ASRP. We will be happy to help.",
    )


async def test_create_contact_message_success(
    client: AsyncClient,
    contact_message_data: dict,
) -> None:
    response = await client.post(
        "/api/contact-messages",
        json=contact_message_data,
    )
    res_data = response.json()

    assert response.status_code == 201
    assert res_data["name"] == contact_message_data["name"]
    assert res_data["email"] == contact_message_data["email"]
    assert res_data["type"] == contact_message_data["type"]
    assert res_data["message_content"] == contact_message_data["message_content"]


async def test_create_get_involved_message_success(
    client: AsyncClient,
    get_involved_message_data: dict,
) -> None:
    response = await client.post(
        "/api/contact-messages",
        json=get_involved_message_data,
    )
    res_data = response.json()

    assert response.status_code == 201
    assert res_data["name"] == get_involved_message_data["name"]
    assert res_data["email"] == get_involved_message_data["email"]
    assert res_data["type"] == get_involved_message_data["type"]
    assert res_data["message_content"] == get_involved_message_data["message_content"]


async def test_create_get_involved_committees_message_success(
    client: AsyncClient,
    get_involved_committees_message_data: dict,
) -> None:
    response = await client.post(
        "/api/contact-messages",
        json=get_involved_committees_message_data,
    )
    res_data = response.json()

    assert response.status_code == 201
    assert res_data["name"] == get_involved_committees_message_data["name"]
    assert res_data["email"] == get_involved_committees_message_data["email"]
    assert res_data["type"] == get_involved_committees_message_data["type"]
    assert res_data["message_content"] == get_involved_committees_message_data["message_content"]


async def test_create_donation_sponsorship_message_success(
    client: AsyncClient,
    donation_sponsorship_message_data: dict,
) -> None:
    response = await client.post(
        "/api/contact-messages",
        json=donation_sponsorship_message_data,
    )
    res_data = response.json()

    assert response.status_code == 201
    assert res_data["name"] == donation_sponsorship_message_data["name"]
    assert res_data["email"] == donation_sponsorship_message_data["email"]
    assert res_data["type"] == donation_sponsorship_message_data["type"]
    assert res_data["message_content"] == donation_sponsorship_message_data["message_content"]
