import pytest
from faker import Faker
from httpx import AsyncClient

from app.core.common.cryptographer import Cryptographer
from app.domains.users.models import User


pytestmark = pytest.mark.anyio


async def test_email_confirm_send(
    client: AsyncClient,
    test_user_with_data: [User, dict],
) -> None:
    _, user_data = test_user_with_data

    response = await client.get(
        "api/auth/email-confirm/send",
        params={"email": user_data["email"]}
    )

    assert response.status_code == 200


async def test_email_confirm_link(
    client: AsyncClient,
    test_user_with_data: [User, dict],
    cryptographer: Cryptographer
) -> None:
    _, user_data = test_user_with_data
    token = cryptographer.create_token(user_data["email"]).decode()

    response = await client.get(
        "api/auth/email-confirm/confirm",
        params={"token": token}
    )

    assert response.status_code == 200


async def test_email_confirm_link_invalid_token(
    client: AsyncClient,
    faker: Faker
) -> None:
    fake_token = faker.pystr()

    response = await client.get(
        "api/auth/email-confirm/confirm",
        params={"token": fake_token}
    )

    assert response.status_code == 400
