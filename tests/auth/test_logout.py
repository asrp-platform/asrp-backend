import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.anyio


async def test_logout(
    client: AsyncClient,
    auth_headers,
    refresh_token,
):
    response = await client.post("api/auth/logout", headers=auth_headers, cookies=refresh_token)

    assert response.status_code == 200
    assert "refresh_token" not in response.cookies


async def test_logout_not_authenticated(
    client: AsyncClient,
) -> None:
    response = await client.post("api/auth/logout")

    assert response.status_code == 401
