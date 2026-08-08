from typing import Any

import pytest
from httpx import AsyncClient

from tests.fixtures.auth import AuthHeaders


pytestmark = pytest.mark.anyio


async def test_create_email_template(
    client: AsyncClient,
    admin_auth_headers: AuthHeaders,
    admin_all_permissions,
    email_template_data: dict[str, Any],
) -> None:
    response = await client.post(
        "/api/admin/email-templates",
        headers=admin_auth_headers,
        json=email_template_data,
    )

    assert response.status_code == 201

    assert response.json().get("name") == email_template_data.get("name")
    assert response.json().get("subject") == email_template_data.get("subject")


async def test_create_email_template_no_permissions(
    client: AsyncClient,
    admin_auth_headers: AuthHeaders,
    email_template_data: dict[str, Any],
) -> None:
    response = await client.post(
        "/api/admin/email-templates",
        headers=admin_auth_headers,
        json=email_template_data,
    )

    assert response.status_code == 403


async def test_create_email_template_by_user(
    client: AsyncClient,
    auth_headers: AuthHeaders,
    email_template_data: dict[str, Any],
) -> None:
    response = await client.post(
        "/api/admin/email-templates",
        headers=auth_headers,
        json=email_template_data,
    )

    assert response.status_code == 403


async def test_create_email_template_not_authorized(
    client: AsyncClient,
    email_template_data: dict[str, Any],
) -> None:
    response = await client.post(
        "/api/admin/email-templates",
        json=email_template_data,
    )

    assert response.status_code == 401


async def test_create_email_template_without_editor_state(
    client: AsyncClient,
    admin_auth_headers: AuthHeaders,
    admin_all_permissions,
    email_template_data: dict[str, Any],
) -> None:
    email_template_data.pop("editor_state")

    response = await client.post(
        "/api/admin/email-templates",
        headers=admin_auth_headers,
        json=email_template_data,
    )

    assert response.status_code == 422


async def test_create_email_template_without_html(
    client: AsyncClient,
    admin_auth_headers: AuthHeaders,
    admin_all_permissions,
    email_template_data: dict[str, Any],
) -> None:
    email_template_data.pop("html")

    response = await client.post(
        "/api/admin/email-templates",
        headers=admin_auth_headers,
        json=email_template_data,
    )

    assert response.status_code == 422
