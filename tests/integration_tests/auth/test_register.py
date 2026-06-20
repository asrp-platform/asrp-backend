from typing import Any
from unittest.mock import AsyncMock, patch

import pytest
from faker import Faker
from httpx import AsyncClient

from app.domains.emails.email_queue import EmailQueue
from app.domains.shared.transaction_managers import TransactionManager

pytestmark = pytest.mark.anyio


async def test_register(
    client: AsyncClient,
    test_transaction_manager: TransactionManager,
    user_registration_data,
) -> None:
    with patch.object(EmailQueue, "send_email", new_callable=AsyncMock) as mock_send_email:
        response = await client.post("api/auth/register", json=user_registration_data)

    async with test_transaction_manager:
        user = await test_transaction_manager.user_repository.get_first_by_kwargs(email=user_registration_data["email"])

    assert response.status_code == 201
    assert user is not None
    mock_send_email.assert_awaited_once()


async def test_register_updates_existing_pending_user(
    client: AsyncClient, test_transaction_manager: TransactionManager, user_data: dict[str, Any]
) -> None:
    user_creation_data = user_data.copy()
    user_creation_data["pending"] = True

    async with test_transaction_manager:
        await test_transaction_manager.user_repository.create(**user_creation_data)

    with patch.object(EmailQueue, "send_email", new_callable=AsyncMock) as mock_send_email:
        response = await client.post("api/auth/register", json={**user_data, "repeat_password": user_data["password"]})

    assert response.status_code == 201
    mock_send_email.assert_awaited_once()


async def test_register_rejects_existing_confirmed_user(
    client: AsyncClient, test_transaction_manager: TransactionManager, user_data: dict[str, Any]
) -> None:
    user_creation_data = user_data.copy()
    user_creation_data["pending"] = False

    async with test_transaction_manager:
        await test_transaction_manager.user_repository.create(**user_creation_data)

    response = await client.post("api/auth/register", json={**user_data, "repeat_password": user_data["password"]})

    assert response.status_code == 409


async def test_password_dont_match(
    client: AsyncClient,
    faker: Faker,
    test_transaction_manager: TransactionManager,
    user_registration_data,
) -> None:
    response = await client.post("api/auth/register", json={**user_registration_data, "repeat_password": faker.pystr()})

    async with test_transaction_manager:
        user = await test_transaction_manager.user_repository.get_first_by_kwargs(email=user_registration_data["email"])

    assert response.status_code == 422
    assert user is None
