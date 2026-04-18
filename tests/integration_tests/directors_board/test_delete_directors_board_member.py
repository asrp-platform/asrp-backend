import pytest
from httpx import AsyncClient

from app.domains.directors_board.models import DirectorBoardMember
from tests.fixtures.auth import AuthHeaders

pytestmark = pytest.mark.anyio


async def test_delete_directors_board_member(
    client: AsyncClient,
    directors_board_member_db: DirectorBoardMember,
    admin_auth_headers: AuthHeaders,
    admin_all_permissions,
) -> None:
    response = await client.delete(
        f"/api/admin/directors-board/{directors_board_member_db.id}",
        headers=admin_auth_headers,
    )

    assert response.status_code == 200
    assert response.json() == directors_board_member_db.id


async def test_delete_directors_board_member_no_permissions(
    client: AsyncClient, directors_board_member_db: DirectorBoardMember, admin_auth_headers: AuthHeaders
) -> None:
    response = await client.delete(
        f"/api/admin/directors-board/{directors_board_member_db.id}",
        headers=admin_auth_headers,
    )

    assert response.status_code == 403


async def test_delete_directors_board_member_by_user(
    client: AsyncClient,
    directors_board_member_db: DirectorBoardMember,
    auth_headers: AuthHeaders,
) -> None:
    response = await client.delete(
        f"/api/admin/directors-board/{directors_board_member_db.id}",
        headers=auth_headers,
    )

    assert response.status_code == 403


async def test_delete_directors_board_member_not_authenticated(
    client: AsyncClient,
    directors_board_member_db: DirectorBoardMember,
) -> None:
    response = await client.delete(
        f"/api/admin/directors-board/{directors_board_member_db.id}",
    )

    assert response.status_code == 401


async def test_delete_directors_board_member_not_found(
    client: AsyncClient,
    admin_auth_headers: AuthHeaders,
    admin_all_permissions,
) -> None:
    response = await client.delete(
        "/api/admin/directors-board/999999",
        headers=admin_auth_headers,
    )

    assert response.status_code == 404
