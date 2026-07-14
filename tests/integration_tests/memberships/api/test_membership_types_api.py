import pytest
from httpx import AsyncClient


pytestmark = pytest.mark.anyio


async def test_get_membership_types(client: AsyncClient) -> None:
    response = await client.get("api/membership-types")
    assert response.status_code == 200
