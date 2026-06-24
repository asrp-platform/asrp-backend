import pytest
from httpx import AsyncClient


pytestmark = pytest.mark.anyio


async def test_get_membership_types(client: AsyncClient) -> None:
    response = await client.get("api/membership-types")

    assert response.status_code == 200

    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0
    assert {
        "id",
        "name",
        "type",
        "price_usd",
        "duration",
        "description",
        "is_purchasable",
    }.issubset(data[0])
