import pytest
from faker import Faker
from fastapi.encoders import jsonable_encoder
from httpx import AsyncClient

from app.domains.directors_board.models import DirectorBoardMember
from tests.fixtures.context import UserContext

pytestmark = pytest.mark.anyio


async def test_update_directors_board_member(
    faker: Faker,
    client: AsyncClient,
    directors_board_member_db: DirectorBoardMember,
    admin_all_permissions_context: UserContext,
) -> None:
    headers, _, _ = admin_all_permissions_context.auth

    request_data = {
        "role": faker.pystr(),
        "name": faker.name(),
        "is_visible": not directors_board_member_db.is_visible,
    }

    response = await client.patch(
        f"/api/admin/directors-board/{directors_board_member_db.id}",
        headers=headers,
        json=jsonable_encoder(request_data),
    )

    assert response.status_code == 200
    assert response.json()["role"] == request_data["role"]
    assert response.json()["name"] == request_data["name"]
    assert response.json()["is_visible"] == request_data["is_visible"]


async def test_update_directors_board_member_no_permissions(
    faker: Faker,
    client: AsyncClient,
    directors_board_member_db: DirectorBoardMember,
    admin_no_permissions_context: UserContext,
) -> None:
    headers, _, _ = admin_no_permissions_context.auth

    request_data = {
        "name": faker.name(),
    }

    response = await client.patch(
        f"/api/admin/directors-board/{directors_board_member_db.id}",
        headers=headers,
        json=jsonable_encoder(request_data),
    )

    assert response.status_code == 403


async def test_update_directors_board_member_by_user(
    faker: Faker,
    client: AsyncClient,
    directors_board_member_db: DirectorBoardMember,
    user_context: UserContext,
) -> None:
    headers, _, _ = user_context.auth

    request_data = {
        "name": faker.name(),
    }

    response = await client.patch(
        f"/api/admin/directors-board/{directors_board_member_db.id}",
        headers=headers,
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
    admin_all_permissions_context: UserContext,
) -> None:
    headers, _, _ = admin_all_permissions_context.auth

    request_data = {
        "name": faker.name(),
    }

    response = await client.patch(
        "/api/admin/directors-board/999999",
        json=jsonable_encoder(request_data),
        headers=headers,
    )

    assert response.status_code == 404
