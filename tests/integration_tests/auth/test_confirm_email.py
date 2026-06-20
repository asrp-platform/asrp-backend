from unittest.mock import AsyncMock, patch

import pytest
from faker import Faker
from httpx import AsyncClient

from app.core.common.cryptographer import Cryptographer
from app.domains.emails.email_queue import EmailQueue
from tests.fixtures.auth import UserFactory

pytestmark = pytest.mark.anyio


async def test_send_email_confirmation_link_for_pending_user(
    client: AsyncClient,
    user_factory: UserFactory,
) -> None:
    test_user = await user_factory(pending=True)

    with patch.object(EmailQueue, "send_email", new_callable=AsyncMock) as mock_send_email:
        response = await client.post("api/auth/email-confirmation-requests", json={"email": test_user.email})

    assert response.status_code == 201
    assert response.json() == {"detail": "Confirmation email sent"}
    mock_send_email.assert_awaited_once()


async def test_send_email_confirmation_link_user_not_found(client: AsyncClient, faker: Faker) -> None:
    response = await client.post("api/auth/email-confirmation-requests", json={"email": faker.email()})

    assert response.status_code == 404
    assert response.json()["detail"] == "User with provided email not found"


async def test_send_email_confirmation_link_for_confirmed_user(
    client: AsyncClient,
    user_factory: UserFactory,
) -> None:
    test_user = await user_factory(pending=False)

    response = await client.post("api/auth/email-confirmation-requests", json={"email": test_user.email})

    assert response.status_code == 409
    assert response.json()["detail"] == "Provided email is already confirmed"


async def test_send_email_confirmation_link_without_body(client: AsyncClient) -> None:
    response = await client.post("api/auth/email-confirmation-requests")

    assert response.status_code == 422


async def test_confirm_email_success(
    client: AsyncClient,
    cryptographer: Cryptographer,
    user_factory: UserFactory,
) -> None:
    test_user = await user_factory(pending=True)
    token = cryptographer.create_token(test_user.email).decode()

    response = await client.get("api/auth/email-confirmations", params={"token": token}, follow_redirects=False)

    assert response.status_code == 200
    assert response.json()["detail"] == "Email successfully confirmed"


async def test_confirm_email_invalid_token(
    client: AsyncClient,
    faker: Faker,
) -> None:
    fake_token = faker.pystr()

    response = await client.get("api/auth/email-confirmations", params={"token": fake_token}, follow_redirects=False)

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid or expired token"


async def test_confirm_email_already_registered(
    client: AsyncClient,
    cryptographer: Cryptographer,
    user_factory: UserFactory,
) -> None:
    test_user = await user_factory(pending=False)
    token = cryptographer.create_token(test_user.email).decode()

    response = await client.get("api/auth/email-confirmations", params={"token": token}, follow_redirects=False)

    assert response.status_code == 409
    assert response.json()["detail"] == "Registration already completed"
