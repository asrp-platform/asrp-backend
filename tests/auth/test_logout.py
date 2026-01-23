import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.anyio


async def test_logout(
    client: AsyncClient,
    user_authentication_data,
):
    authorization_header, refresh_token_cookie, _ = user_authentication_data

    response = await client.post("api/auth/logout", headers=authorization_header, cookies=refresh_token_cookie)

    assert response.status_code == 200
    assert "refresh_token" not in response.cookies


async def test_logout_not_authenticated(
    client: AsyncClient,
) -> None:
    response = await client.post("api/auth/logout")

    assert response.status_code == 401
