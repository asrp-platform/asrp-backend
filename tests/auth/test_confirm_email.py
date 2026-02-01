import pytest
from faker import Faker
from httpx import AsyncClient

from app.core.common.cryptographer import Cryptographer
from app.domains.users.models import User

pytestmark = pytest.mark.anyio


async def test_send_link_for_confirm_email(
    client: AsyncClient,
    test_user_with_data: [User, dict],
) -> None:
    _, user_data = test_user_with_data

    response = await client.post(
        "api/auth/email-confirm",
        params={"email": user_data["email"]}
    )

    assert response.status_code == 201


async def test_confirm_email(
    client: AsyncClient,
    test_user_with_data: [User, dict],
    cryptographer: Cryptographer
) -> None:
    _, user_data = test_user_with_data
    token = cryptographer.create_token(user_data["email"]).decode()

    response = await client.patch(
        "api/auth/email-confirm/confirm",
        params={"token": token}
    )

    assert response.status_code == 204


async def test_confirm_email_invalid_token(
    client: AsyncClient,
    faker: Faker
) -> None:
    fake_token = faker.pystr()

    response = await client.patch(
        "api/auth/email-confirm/confirm",
        params={"token": fake_token}
    )

    assert response.status_code == 400
