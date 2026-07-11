import pytest
from faker import Faker
from fastapi.encoders import jsonable_encoder
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.directors_board.models import DirectorBoardMember
from tests.fixtures.auth import AuthHeaders


pytestmark = pytest.mark.anyio


async def test_update_directors_board_member(
    faker: Faker,
    client: AsyncClient,
    directors_board_member_db: DirectorBoardMember,
    admin_auth_headers: AuthHeaders,
    admin_all_permissions,
) -> None:
    request_data = {
        "role": faker.pystr(),
        "name": faker.name(),
        "is_visible": not directors_board_member_db.is_visible,
    }

    response = await client.patch(
        f"/api/admin/directors-board/{directors_board_member_db.id}",
        headers=admin_auth_headers,
        json=jsonable_encoder(request_data),
    )

    assert response.status_code == 200
    assert response.json()["role"] == request_data["role"]
    assert response.json()["name"] == request_data["name"]
    assert response.json()["is_visible"] == request_data["is_visible"]


async def test_update_directors_board_member_returns_full_photo_url(
    client: AsyncClient,
    test_session: AsyncSession,
    file_storage,
    spy_file_storage,
    directors_board_member_db: DirectorBoardMember,
    admin_auth_headers: AuthHeaders,
    admin_all_permissions,
) -> None:
    object_key = "directors_board/updated-photo.png"
    await file_storage.upload_file(object_key=object_key, file_content=b"fake image content")

    response = await client.patch(
        f"/api/admin/directors-board/{directors_board_member_db.id}",
        headers=admin_auth_headers,
        json={"photo_url": object_key},
    )

    assert response.status_code == 200
    assert response.json()["photo_url"].startswith("http")

    stored_member = (
        await test_session.execute(
            select(DirectorBoardMember).where(DirectorBoardMember.id == directors_board_member_db.id)
        )
    ).scalar_one()
    assert stored_member.photo_url == object_key
    spy_file_storage["get_file_url"].assert_any_await(object_key)


async def test_update_directors_board_member_no_permissions(
    faker: Faker,
    client: AsyncClient,
    directors_board_member_db: DirectorBoardMember,
    admin_auth_headers: AuthHeaders,
) -> None:
    request_data = {
        "name": faker.name(),
    }

    response = await client.patch(
        f"/api/admin/directors-board/{directors_board_member_db.id}",
        headers=admin_auth_headers,
        json=jsonable_encoder(request_data),
    )

    assert response.status_code == 403


async def test_update_directors_board_member_by_user(
    faker: Faker,
    client: AsyncClient,
    directors_board_member_db: DirectorBoardMember,
    auth_headers: AuthHeaders,
) -> None:
    request_data = {
        "name": faker.name(),
    }

    response = await client.patch(
        f"/api/admin/directors-board/{directors_board_member_db.id}",
        headers=auth_headers,
        json=jsonable_encoder(request_data),
    )

    assert response.status_code == 403


async def test_update_directors_board_member_not_authenticated(
    faker: Faker,
    client: AsyncClient,
    directors_board_member_db: DirectorBoardMember,
) -> None:
    request_data = {
        "name": faker.name(),
    }

    response = await client.patch(
        f"/api/admin/directors-board/{directors_board_member_db.id}",
        json=jsonable_encoder(request_data),
    )

    assert response.status_code == 401


async def test_delete_directors_board_member_not_found(
    faker: Faker,
    client: AsyncClient,
    directors_board_member_db: DirectorBoardMember,
    admin_auth_headers: AuthHeaders,
    admin_all_permissions,
) -> None:
    request_data = {
        "name": faker.name(),
    }

    response = await client.patch(
        "/api/admin/directors-board/999999",
        json=jsonable_encoder(request_data),
        headers=admin_auth_headers,
    )

    assert response.status_code == 404
