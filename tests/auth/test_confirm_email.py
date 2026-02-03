import pytest
from faker import Faker
from httpx import AsyncClient

from app.core.common.cryptographer import Cryptographer
from app.domains.users.models import User

pytestmark = pytest.mark.anyio


async def test_send_link_for_confirm_email(
    client: AsyncClient,
    user_authentication_data
) -> None:
    authorization_header, _, _ = user_authentication_data

    response = await client.post(
        "api/auth/email-confirm",
        headers=authorization_header
    )

    assert response.status_code == 201


async def test_confirm_email(
    client: AsyncClient,
    cryptographer: Cryptographer,
    user_authentication_data
) -> None:
    authorization_header, _, email = user_authentication_data
    token = cryptographer.create_token(email).decode()

    response = await client.patch(
        "api/auth/email-confirm/confirm",
        headers=authorization_header,
        params={"token": token}
    )

    assert response.status_code == 204


async def test_confirm_email_invalid_token(
    client: AsyncClient,
    faker: Faker,
    user_authentication_data
) -> None:
    authorization_header, _, _ = user_authentication_data
    fake_token = faker.pystr()

    response = await client.patch(
        "api/auth/email-confirm/confirm",
        headers=authorization_header,
        params={"token": fake_token}
    )

    assert response.status_code == 401


async def test_send_link_for_confirm_email_not_authenticated(
    client: AsyncClient,
) -> None:

    response = await client.post(
        "api/auth/email-confirm",
    )

    assert response.status_code == 401


async def test_confirm_email_not_authenticated(
    client: AsyncClient,
    cryptographer: Cryptographer,
    test_user_with_data: [User, dict],
) -> None:
    _, user_data = test_user_with_data
    token = cryptographer.create_token(user_data["email"]).decode()

    response = await client.patch(
        "api/auth/email-confirm/confirm",
        params={"token": token}
    )

    assert response.status_code == 401


async def test_confirm_email_with_different_emails_in_tokens(
    client: AsyncClient,
    cryptographer: Cryptographer,
    faker: Faker,
    user_authentication_data
) -> None:
    authorization_header, _, _ = user_authentication_data

    email = faker.email()
    token = cryptographer.create_token(email).decode()

    response = await client.patch(
        "api/auth/email-confirm/confirm",
        headers=authorization_header,
        params={"token": token}
    )

    assert response.status_code == 401
