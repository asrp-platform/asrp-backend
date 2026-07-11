from typing import Any

import pytest
from httpx import AsyncClient

from tests.fixtures.auth import AuthHeaders


pytestmark = pytest.mark.anyio


@pytest.mark.parametrize(
    ("country", "error_message", "address_data"),
    [
        ("US", "State is required for USA", {"postal_code": "10001"}),
        ("US", "Postal code is required for USA", {"state": "NY"}),
        ("USA", "State is required for USA", {"postal_code": "10001"}),
        ("USA", "Postal code is required for USA", {"state": "NY"}),
    ],
)
async def test_update_current_user_requires_state_and_postal_code_for_usa(
    client: AsyncClient,
    auth_headers: AuthHeaders,
    country: str,
    error_message: str,
    address_data: dict[str, str],
) -> None:
    payload = {
        "country": country,
        "city": "New York",
        **address_data,
    }

    response = await client.patch("/api/users/current-user", json=payload, headers=auth_headers)

    assert response.status_code == 422
    assert error_message in response.text


async def test_update_current_user_allows_missing_state_and_postal_code_for_non_usa(
    client: AsyncClient,
    auth_headers: AuthHeaders,
) -> None:
    payload = {
        "country": "CA",
        "city": "Toronto",
    }

    response = await client.patch("/api/users/current-user", json=payload, headers=auth_headers)

    assert response.status_code == 200


async def test_update_current_user_allows_usa_with_state_and_postal_code(
    client: AsyncClient,
    auth_headers: AuthHeaders,
) -> None:
    payload = {
        "country": "US",
        "city": "New York",
        "state": "NY",
        "postal_code": "10001",
    }

    response = await client.patch("/api/users/current-user", json=payload, headers=auth_headers)

    assert response.status_code == 200


async def test_update_current_user_allows_partial_update_without_country(
    client: AsyncClient,
    auth_headers: AuthHeaders,
) -> None:
    payload: dict[str, Any] = {
        "preferred_name": "Max",
    }

    response = await client.patch("/api/users/current-user", json=payload, headers=auth_headers)

    assert response.status_code == 200
