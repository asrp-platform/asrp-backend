from typing import Any

import pytest
from fastapi.encoders import jsonable_encoder
from httpx import AsyncClient

from tests.fixtures.context import UserContext

pytestmark = pytest.mark.anyio


async def test_create_directors_board_member(
    client: AsyncClient, directors_board_member_data: dict[str, Any], admin_all_permissions_context: UserContext
) -> None:
    headers, _, _ = admin_all_permissions_context.auth

    response = await client.post(
        "/api/admin/directors-board",
        headers=headers,
        json=jsonable_encoder(directors_board_member_data),
    )

    assert response.status_code == 201


async def test_create_directors_board_member_no_permissions(
    client: AsyncClient, directors_board_member_data: dict[str, Any], admin_no_permissions_context: UserContext
) -> None:
    headers, _, _ = admin_no_permissions_context.auth

    response = await client.post(
        "/api/admin/directors-board",
        headers=headers,
        json=jsonable_encoder(directors_board_member_data),
    )

    assert response.status_code == 403


async def test_create_directors_board_member_not_authorized(
    client: AsyncClient, directors_board_member_data: dict[str, Any], admin_no_permissions_context: UserContext
) -> None:
    headers, _, _ = admin_no_permissions_context.auth

    response = await client.post(
        "/api/admin/directors-board",
        headers=headers,
        json=jsonable_encoder(directors_board_member_data),
    )

    assert response.status_code == 403


async def test_create_directors_board_member_by_user(
    client: AsyncClient,
    directors_board_member_data: dict[str, Any],
    user_context: UserContext,
) -> None:
    headers, _, _ = user_context.auth

    response = await client.post(
        "/api/admin/directors-board",
        headers=headers,
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
