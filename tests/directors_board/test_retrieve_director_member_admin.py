import pytest
from httpx import AsyncClient

from tests.fixtures.context import UserContext

pytestmark = pytest.mark.anyio


async def test_retrieve_public_directors_board_by_user(
    client: AsyncClient,
) -> None:
    response = await client.get("/api/directors-board")

    assert response.status_code == 200


async def test_retrieve_directors_board_by_admin(
    client: AsyncClient,
    admin_all_permissions_context: UserContext,
) -> None:
    headers, _, _ = admin_all_permissions_context.auth

    response = await client.get("/api/admin/directors-board", headers=headers)

    assert response.status_code == 200


async def test_retrieve_directors_board_by_user(
    client: AsyncClient,
    user_context: UserContext,
) -> None:
    headers, _, _ = user_context.auth

    response = await client.get("/api/admin/directors-board", headers=headers)

    assert response.status_code == 403


async def test_retrieve_directors_board_not_authorized(
    client: AsyncClient,
    admin_no_permissions_context: UserContext,
) -> None:
    headers, cookies, email = admin_no_permissions_context.auth

    response = await client.get("/api/admin/directors-board", headers={**headers})

    assert response.status_code == 403


async def test_retrieve_directors_board_not_authenticated(
    client: AsyncClient,
) -> None:
    response = await client.get("/api/admin/directors-board")

    assert response.status_code == 401
