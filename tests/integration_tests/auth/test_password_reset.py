from unittest.mock import AsyncMock, patch

import pytest
from httpx import AsyncClient

from app.core.common.cryptographer import Cryptographer
from app.core.config import fernet
from app.domains.emails.email_queue import EmailQueue
from tests.fixtures.test_transaction_manager import TransactionManager


pytestmark = pytest.mark.anyio


async def test_password_reset_request_sends_email(client: AsyncClient, user_factory) -> None:
    user = await user_factory(pending=False)

    with patch.object(EmailQueue, "send_email", new_callable=AsyncMock) as send_email:
        response = await client.post("api/auth/password-reset", json={"email": user.email})

    assert response.status_code == 202
    send_email.assert_awaited_once()


async def test_password_reset_request_does_not_reveal_unknown_email(client: AsyncClient, faker) -> None:
    with patch.object(EmailQueue, "send_email", new_callable=AsyncMock) as send_email:
        response = await client.post("api/auth/password-reset", json={"email": faker.email()})

    assert response.status_code == 202
    send_email.assert_not_awaited()


async def test_password_reset_changes_password(
    client: AsyncClient,
    user_factory,
    test_transaction_manager: TransactionManager,
) -> None:
    old_password = "old-password-123"
    user = await user_factory(pending=False, password=old_password)
    token = Cryptographer(fernet).create_token(user.email).decode()
    new_password = "new-password-123"

    response = await client.post(
        "api/auth/password-reset/confirm",
        params={"token": token},
        json={"password": new_password, "confirm_password": new_password},
    )

    assert response.status_code == 204

    async with test_transaction_manager:
        updated_user = await test_transaction_manager.user_repository.get_by_email(user.email)
    assert updated_user.last_password_change is not None

    old_login_response = await client.post(
        "api/auth/login",
        json={"email": user.email, "password": old_password},
    )
    assert old_login_response.status_code == 401

    login_response = await client.post(
        "api/auth/login",
        json={"email": user.email, "password": new_password},
    )
    assert login_response.status_code == 200


async def test_password_reset_token_can_be_verified(
    client: AsyncClient,
    user_factory,
) -> None:
    user = await user_factory(pending=False)
    token = Cryptographer(fernet).create_token(user.email).decode()

    response = await client.get("api/auth/password-reset/verify", params={"token": token})

    assert response.status_code == 200
    assert response.json() == user.email


async def test_password_reset_token_verification_rejects_invalid_token(
    client: AsyncClient,
) -> None:
    response = await client.get("api/auth/password-reset/verify", params={"token": "invalid-token"})

    assert response.status_code == 400
    assert response.json()["detail"] == "Invalid token"


async def test_password_reset_rejects_invalid_token(client: AsyncClient) -> None:
    response = await client.post(
        "api/auth/password-reset/confirm",
        params={"token": "invalid-token"},
        json={"password": "new-password-123", "confirm_password": "new-password-123"},
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Invalid token"
