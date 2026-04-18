import pytest
from faker import Faker
from httpx import AsyncClient

from app.core.common.cryptographer import Cryptographer
from app.domains.users.models import User

pytestmark = pytest.mark.anyio


async def test_send_email_confirmation_link(
    client: AsyncClient,
    auth_headers,
) -> None:
    response = await client.post("api/auth/email-confirmation-requests", headers=auth_headers)

    assert response.status_code == 201


async def test_confirm_email(client: AsyncClient, cryptographer: Cryptographer, auth_headers, test_user: User) -> None:
    token = cryptographer.create_token(test_user.email).decode()

    response = await client.post("api/auth/email-confirmations", headers=auth_headers, params={"token": token})

    assert response.status_code == 204


async def test_confirm_email_invalid_token(
    client: AsyncClient,
    faker: Faker,
    auth_headers,
) -> None:
    fake_token = faker.pystr()

    response = await client.post("api/auth/email-confirmations", headers=auth_headers, params={"token": fake_token})

    assert response.status_code == 401


async def test_send_link_for_confirm_email_not_authenticated(
    client: AsyncClient,
) -> None:
    response = await client.post(
        "api/auth/email-confirmation-requests",
    )

    assert response.status_code == 401


async def test_confirm_email_not_authenticated(
    client: AsyncClient, cryptographer: Cryptographer, test_user: User
) -> None:
    token = cryptographer.create_token(test_user.email).decode()

    response = await client.post("api/auth/email-confirmations", params={"token": token})

    assert response.status_code == 401


async def test_confirm_email_with_different_emails_in_tokens(
    client: AsyncClient,
    cryptographer: Cryptographer,
    faker: Faker,
    auth_headers,
) -> None:
    email = faker.email()
    token = cryptographer.create_token(email).decode()

    response = await client.post("api/auth/email-confirmations", headers=auth_headers, params={"token": token})

    assert response.status_code == 401
