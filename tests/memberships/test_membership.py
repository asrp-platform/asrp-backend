import pytest
from httpx import AsyncClient

from app.domains.memberships.models import UserMembership
from tests.fixtures.auth import AuthHeaders

pytestmark = pytest.mark.anyio


async def test_create_membership(
    client: AsyncClient,
    auth_headers: AuthHeaders,
    membership_data: dict
) -> None:
    response = await client.post(
        "api/memberships",
        headers=auth_headers,
        json=membership_data
    )

    assert response.status_code == 201


async def test_create_membership_not_authenticated(
    client: AsyncClient,
    membership_data: dict
) -> None:
    response = await client.post(
        "api/memberships",
        json=membership_data
    )

    assert response.status_code == 401


async def test_create_membership_already_exists(
    client: AsyncClient,
    membership: UserMembership,
    auth_headers: AuthHeaders,
    membership_data: dict
) -> None:
    response = await client.post(
        "api/memberships",
        headers=auth_headers,
        json=membership_data
    )

    assert response.status_code == 409
