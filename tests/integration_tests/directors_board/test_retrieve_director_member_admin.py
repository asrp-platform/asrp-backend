import pytest
from httpx import AsyncClient
from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.directors_board.models import DirectorBoardMember
from tests.fixtures.auth import AuthHeaders

pytestmark = pytest.mark.anyio


async def test_retrieve_public_directors_board_by_user(
    client: AsyncClient,
    test_session: AsyncSession,
    directors_board_member_db,
    spy_file_storage,
) -> None:
    photo_object_key = "directors_board/photo.png"
    await test_session.execute(
        update(DirectorBoardMember)
        .where(DirectorBoardMember.id == directors_board_member_db.id)
        .values(photo_url=photo_object_key)
    )
    await test_session.flush()

    expected_photo_url = "https://example-r2.test/directors_board/photo.png"
    spy_file_storage["get_file_url"].return_value = expected_photo_url

    response = await client.get("/api/directors-board")
    data = response.json()

    assert response.status_code == 200
    assert data[0]["photo_url"] == expected_photo_url
    spy_file_storage["get_file_url"].assert_awaited_once_with(photo_object_key)


async def test_retrieve_directors_board_by_admin(
    client: AsyncClient, admin_auth_headers: AuthHeaders, admin_all_permissions, directors_board_member_db
) -> None:
    response = await client.get("/api/admin/directors-board", headers=admin_auth_headers)

    assert response.status_code == 200


async def test_retrieve_directors_board_by_user(
    client: AsyncClient,
    auth_headers: AuthHeaders,
    directors_board_member_db,
) -> None:
    response = await client.get("/api/admin/directors-board", headers=auth_headers)

    assert response.status_code == 403


async def test_retrieve_directors_board_not_authorized(
    client: AsyncClient,
    admin_auth_headers: AuthHeaders,
) -> None:
    response = await client.get("/api/admin/directors-board", headers=admin_auth_headers)

    assert response.status_code == 200


async def test_retrieve_directors_board_not_authenticated(
    client: AsyncClient,
) -> None:
    response = await client.get("/api/admin/directors-board")

    assert response.status_code == 401
