import io

import pytest
from httpx import AsyncClient

from tests.fixtures.auth import AuthHeaders

pytestmark = pytest.mark.anyio


@pytest.fixture
def image_file():
    return io.BytesIO(b"fake image content")


async def test_upload_director_member_photo(
    client: AsyncClient,
    admin_auth_headers: AuthHeaders,
    admin_all_permissions,
    image_file,
    mock_s3_storage,
) -> None:
    response = await client.post(
        "/api/admin/directors-board/images",
        headers=admin_auth_headers,
        files={
            "file": ("photo.png", image_file, "image/png"),
        },
    )

    assert response.status_code == 201
    assert "path" in response.json()
    assert response.json()["path"].startswith("directors_board/")
    assert mock_s3_storage.upload_file.called


async def test_upload_director_member_photo_no_permissions(
    client: AsyncClient,
    admin_auth_headers: AuthHeaders,
    image_file,
) -> None:
    response = await client.post(
        "/api/admin/directors-board/images",
        headers=admin_auth_headers,
        files={
            "file": ("photo.png", image_file, "image/png"),
        },
    )

    assert response.status_code == 403


async def test_upload_director_member_photo_by_user(
    client: AsyncClient,
    auth_headers: AuthHeaders,
    image_file,
) -> None:
    response = await client.post(
        "/api/admin/directors-board/images",
        headers=auth_headers,
        files={
            "file": ("photo.png", image_file, "image/png"),
        },
    )

    assert response.status_code == 403


async def test_upload_director_member_photo_not_authenticated(
    client: AsyncClient,
    image_file,
) -> None:
    response = await client.post(
        "/api/admin/directors-board/images",
        files={
            "file": ("photo.png", image_file, "image/png"),
        },
    )

    assert response.status_code == 401


async def test_upload_director_member_photo_invalid_content_type(
    client: AsyncClient,
    admin_auth_headers: AuthHeaders,
    admin_all_permissions,
) -> None:
    fake_file = io.BytesIO(b"not an image")

    response = await client.post(
        "/api/admin/directors-board/images",
        headers=admin_auth_headers,
        files={
            "file": ("file.txt", fake_file, "text/plain"),
        },
    )

    assert response.status_code == 415
