import pytest
from httpx import AsyncClient

from tests.fixtures.auth import AuthHeaders

pytestmark = pytest.mark.anyio


async def test_retrieve_public_directors_board_by_user(
    client: AsyncClient,
) -> None:
    response = await client.get("/api/directors-board")

    assert response.status_code == 200


async def test_retrieve_directors_board_by_admin(
    client: AsyncClient,
    admin_auth_headers: AuthHeaders,
    admin_all_permissions,
) -> None:
    response = await client.get("/api/admin/directors-board", headers=admin_auth_headers)

    assert response.status_code == 200


async def test_retrieve_directors_board_by_user(client: AsyncClient, auth_headers: AuthHeaders) -> None:
    response = await client.get("/api/admin/directors-board", headers=auth_headers)

    assert response.status_code == 403


async def test_retrieve_directors_board_not_authorized(
    client: AsyncClient,
    admin_auth_headers: AuthHeaders,
) -> None:
    response = await client.get("/api/admin/directors-board", headers=admin_auth_headers)

    assert response.status_code == 403


async def test_retrieve_directors_board_not_authenticated(
    client: AsyncClient,
) -> None:
    response = await client.get("/api/admin/directors-board")

    assert response.status_code == 401
