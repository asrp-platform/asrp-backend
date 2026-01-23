import io

import pytest
from httpx import AsyncClient

from tests.fixtures.context import UserContext

pytestmark = pytest.mark.anyio


@pytest.fixture
def image_file():
    return io.BytesIO(b"fake image content")


async def test_upload_director_member_photo(
    client: AsyncClient,
    admin_all_permissions_context: UserContext,
    image_file,
) -> None:
    headers, _, _ = admin_all_permissions_context.auth

    response = await client.post(
        "/api/admin/directors-board/images",
        headers=headers,
        files={
            "file": ("photo.png", image_file, "image/png"),
        },
    )

    assert response.status_code == 200
    assert "path" in response.json()
    assert response.json()["path"].endswith(".png")


async def test_upload_director_member_photo_no_permissions(
    client: AsyncClient,
    admin_no_permissions_context: UserContext,
    image_file,
) -> None:
    headers, _, _ = admin_no_permissions_context.auth

    response = await client.post(
        "/api/admin/directors-board/images",
        headers=headers,
        files={
            "file": ("photo.png", image_file, "image/png"),
        },
    )

    assert response.status_code == 403


async def test_upload_director_member_photo_by_user(
    client: AsyncClient,
    user_context: UserContext,
    image_file,
) -> None:
    headers, _, _ = user_context.auth

    response = await client.post(
        "/api/admin/directors-board/images",
        headers=headers,
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
    admin_all_permissions_context: UserContext,
) -> None:
    headers, _, _ = admin_all_permissions_context.auth

    fake_file = io.BytesIO(b"not an image")

    response = await client.post(
        "/api/admin/directors-board/images",
        headers=headers,
        files={
            "file": ("file.txt", fake_file, "text/plain"),
        },
    )

    assert response.status_code == 415
