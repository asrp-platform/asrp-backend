from typing import Any

import pytest
from fastapi.encoders import jsonable_encoder
from httpx import AsyncClient

from tests.fixtures.auth import AuthHeaders

pytestmark = pytest.mark.anyio


async def test_create_directors_board_member(
    client: AsyncClient,
    admin_auth_headers: AuthHeaders,
    admin_all_permissions,
    directors_board_member_data: dict[str, Any],
) -> None:
    response = await client.post(
        "/api/admin/directors-board",
        headers=admin_auth_headers,
        json=jsonable_encoder(directors_board_member_data),
    )

    assert response.status_code == 201


async def test_create_directors_board_member_no_permissions(
    client: AsyncClient,
    admin_auth_headers: AuthHeaders,
    directors_board_member_data: dict[str, Any],
) -> None:
    response = await client.post(
        "/api/admin/directors-board",
        headers=admin_auth_headers,
        json=jsonable_encoder(directors_board_member_data),
    )

    assert response.status_code == 403


async def test_create_directors_board_member_not_authorized(
    client: AsyncClient,
    directors_board_member_data: dict[str, Any],
    auth_headers: AuthHeaders,
) -> None:
    response = await client.post(
        "/api/admin/directors-board",
        headers=auth_headers,
        json=jsonable_encoder(directors_board_member_data),
    )

    assert response.status_code == 403


async def test_create_directors_board_not_authenticated(
    client: AsyncClient,
    directors_board_member_data: dict[str, Any],
) -> None:
    response = await client.post(
        "/api/admin/directors-board",
        json=jsonable_encoder(directors_board_member_data),
    )

    assert response.status_code == 401
