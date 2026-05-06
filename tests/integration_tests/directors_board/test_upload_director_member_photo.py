from io import BytesIO

import pytest
from faker import Faker
from httpx import AsyncClient

from tests.fixtures.auth import AuthHeaders

pytestmark = pytest.mark.anyio


@pytest.fixture
def fake_file(faker: Faker):
    return BytesIO(faker.binary(length=1024))


async def test_upload_director_member_photo(
    client: AsyncClient,
    admin_auth_headers: AuthHeaders,
    admin_all_permissions,
    fake_file,
    spy_file_storage,
) -> None:
    response = await client.put(
        "/api/admin/directors-board/images",
        headers=admin_auth_headers,
        files={
            "file": ("photo.png", fake_file, "image/png"),
        },
    )

    data = response.json()

    assert response.status_code == 200
    assert "path" in data
    assert "directors_board" in data["path"].split("/")

    spy_file_storage["upload_file"].assert_awaited_once()


async def test_upload_director_member_photo_no_permissions(
    client: AsyncClient,
    admin_auth_headers: AuthHeaders,
    fake_file,
        spy_file_storage,
) -> None:
    response = await client.put(
        "/api/admin/directors-board/images",
        headers=admin_auth_headers,
        files={
            "file": ("photo.png", fake_file, "image/png"),
        },
    )

    assert response.status_code == 403

    spy_file_storage["upload_file"].assert_not_awaited()


async def test_upload_director_member_photo_by_user(
    client: AsyncClient,
    auth_headers: AuthHeaders,
    fake_file,
        spy_file_storage,
) -> None:
    response = await client.put(
        "/api/admin/directors-board/images",
        headers=auth_headers,
        files={
            "file": ("photo.png", fake_file, "image/png"),
        },
    )

    assert response.status_code == 403

    spy_file_storage["upload_file"].assert_not_awaited()


async def test_upload_director_member_photo_not_authenticated(
    client: AsyncClient,
    fake_file,
        spy_file_storage,
) -> None:
    response = await client.put(
        "/api/admin/directors-board/images",
        files={
            "file": ("photo.png", fake_file, "image/png"),
        },
    )

    assert response.status_code == 401

    spy_file_storage["upload_file"].assert_not_awaited()


async def test_upload_director_member_photo_invalid_content_type(
    client: AsyncClient,
    admin_auth_headers: AuthHeaders,
    admin_all_permissions,
    fake_file,
        spy_file_storage,
) -> None:
    response = await client.put(
        "/api/admin/directors-board/images",
        headers=admin_auth_headers,
        files={
            "file": ("file.txt", fake_file, "text/plain"),
        },
    )

    assert response.status_code == 415

    spy_file_storage["upload_file"].assert_not_awaited()
