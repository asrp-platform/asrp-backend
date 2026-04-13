import pytest
from httpx import AsyncClient

from app.domains.directors_board.models import DirectorBoardMember
from tests.fixtures.auth import AuthHeaders

pytestmark = pytest.mark.anyio


async def test_delete_director_member_photo(
    client: AsyncClient,
    directors_board_member_db: DirectorBoardMember,
    admin_auth_headers: AuthHeaders,
    admin_all_permissions,
    mock_s3_storage,
) -> None:
    response = await client.delete(
        f"/api/admin/directors-board/{directors_board_member_db.id}/image",
        headers=admin_auth_headers,
    )

    assert response.status_code == 204
    assert mock_s3_storage.delete_object.called
    assert directors_board_member_db.photo_url is None


async def test_delete_director_member_photo_no_permissions(
    client: AsyncClient,
    directors_board_member_db: DirectorBoardMember,
    admin_auth_headers: AuthHeaders,
    mock_s3_storage,
) -> None:
    response = await client.delete(
        f"/api/admin/directors-board/{directors_board_member_db.id}/image",
        headers=admin_auth_headers,
    )

    assert response.status_code == 403
    assert not mock_s3_storage.delete_object.called


async def test_delete_director_member_photo_not_found(
    client: AsyncClient,
    admin_auth_headers: AuthHeaders,
    admin_all_permissions,
) -> None:
    response = await client.delete(
        "/api/admin/directors-board/999999/image",
        headers=admin_auth_headers,
    )

    assert response.status_code == 404
