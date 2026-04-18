import io

import pytest
from httpx import AsyncClient

from app.domains.directors_board.models import DirectorBoardMember
from tests.fixtures.auth import AuthHeaders

pytestmark = pytest.mark.anyio


@pytest.fixture
def image_file():
    return io.BytesIO(b"fake image content")


async def test_upload_director_member_photo(
    client: AsyncClient,
    directors_board_member_db: DirectorBoardMember,
    admin_auth_headers: AuthHeaders,
    admin_all_permissions,
    image_file,
    mock_s3_storage,
) -> None:
    response = await client.post(
        f"/api/admin/directors-board/{directors_board_member_db.id}/image",
        headers=admin_auth_headers,
        files={
            "file": ("photo.png", image_file, "image/png"),
        },
    )

    assert response.status_code == 201
    data = response.json()
    assert "path" in data
    assert "presigned_url" in data
    assert data["path"].startswith("directors_board/")
    assert data["presigned_url"] is not None
    assert mock_s3_storage.upload_file.called


async def test_upload_director_member_photo_no_permissions(
    client: AsyncClient,
    directors_board_member_db: DirectorBoardMember,
    admin_auth_headers: AuthHeaders,
    image_file,
) -> None:
    response = await client.post(
        f"/api/admin/directors-board/{directors_board_member_db.id}/image",
        headers=admin_auth_headers,
        files={
            "file": ("photo.png", image_file, "image/png"),
        },
    )

    assert response.status_code == 403


async def test_upload_director_member_photo_by_user(
    client: AsyncClient,
    directors_board_member_db: DirectorBoardMember,
    auth_headers: AuthHeaders,
    image_file,
) -> None:
    response = await client.post(
        f"/api/admin/directors-board/{directors_board_member_db.id}/image",
        headers=auth_headers,
        files={
            "file": ("photo.png", image_file, "image/png"),
        },
    )

    assert response.status_code == 403


async def test_upload_director_member_photo_not_authenticated(
    client: AsyncClient,
    directors_board_member_db: DirectorBoardMember,
    image_file,
) -> None:
    response = await client.post(
        f"/api/admin/directors-board/{directors_board_member_db.id}/image",
        files={
            "file": ("photo.png", image_file, "image/png"),
        },
    )

    assert response.status_code == 401


async def test_upload_director_member_photo_invalid_content_type(
    client: AsyncClient,
    directors_board_member_db: DirectorBoardMember,
    admin_auth_headers: AuthHeaders,
    admin_all_permissions,
) -> None:
    fake_file = io.BytesIO(b"not an image")

    response = await client.post(
        f"/api/admin/directors-board/{directors_board_member_db.id}/image",
        headers=admin_auth_headers,
        files={
            "file": ("file.txt", fake_file, "text/plain"),
        },
    )

    assert response.status_code == 415
