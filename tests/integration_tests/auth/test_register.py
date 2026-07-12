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
        communication_preferences = (
            await test_transaction_manager.communication_preferences_repository.get_first_by_kwargs(user_id=user.id)
        )

    assert response.status_code == 201
    assert user is not None
    assert communication_preferences is not None
    assert communication_preferences.user_id == user.id
    assert not communication_preferences.newsletters
    assert not communication_preferences.events_meetings
    assert not communication_preferences.committees_leadership
    assert not communication_preferences.volunteer_opportunities
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


@pytest.mark.parametrize(
    ("country", "error_message", "address_data"),
    [
        ("US", "State is required for USA", {"postal_code": "10001"}),
        ("US", "Postal code is required for USA", {"state": "NY"}),
        ("USA", "State is required for USA", {"postal_code": "10001"}),
        ("USA", "Postal code is required for USA", {"state": "NY"}),
    ],
)
async def test_register_requires_state_and_postal_code_for_usa(
    client: AsyncClient,
    test_transaction_manager: TransactionManager,
    user_registration_data: dict[str, Any],
    country: str,
    error_message: str,
    address_data: dict[str, str],
) -> None:
    payload = {
        **user_registration_data,
        "country": country,
        **address_data,
    }

    with patch.object(EmailQueue, "send_email", new_callable=AsyncMock) as mock_send_email:
        response = await client.post("api/auth/register", json=payload)

    async with test_transaction_manager:
        user = await test_transaction_manager.user_repository.get_first_by_kwargs(email=payload["email"])

    assert response.status_code == 422
    assert error_message in response.text
    assert user is None
    mock_send_email.assert_not_awaited()


async def test_register_allows_missing_state_and_postal_code_for_non_usa(
    client: AsyncClient,
    test_transaction_manager: TransactionManager,
    user_registration_data: dict[str, Any],
) -> None:
    payload = {**user_registration_data, "country": "CA"}
    payload.pop("state", None)
    payload.pop("postal_code", None)

    with patch.object(EmailQueue, "send_email", new_callable=AsyncMock) as mock_send_email:
        response = await client.post("api/auth/register", json=payload)

    async with test_transaction_manager:
        user = await test_transaction_manager.user_repository.get_first_by_kwargs(email=payload["email"])

    assert response.status_code == 201
    assert user is not None
    assert user.state is None
    assert user.postal_code is None
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
