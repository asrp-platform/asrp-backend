from dataclasses import asdict

import pytest
from httpx import AsyncClient

from app.domains.emails.common.variables import VARIABLES_LIST
from tests.fixtures.auth import AuthHeaders


pytestmark = pytest.mark.anyio


async def test_get_email_template_variables(
    client: AsyncClient,
    admin_auth_headers: AuthHeaders,
    admin_all_permissions,
) -> None:
    response = await client.get(
        "/api/admin/email-templates/variables",
        headers=admin_auth_headers,
    )

    assert response.status_code == 200
    assert response.json() == [asdict(variable) for variable in VARIABLES_LIST]


async def test_get_email_template_variables_no_permissions(
    client: AsyncClient,
    admin_auth_headers: AuthHeaders,
) -> None:
    response = await client.get(
        "/api/admin/email-templates/variables",
        headers=admin_auth_headers,
    )

    assert response.status_code == 403


async def test_get_email_template_variables_by_user(
    client: AsyncClient,
    auth_headers: AuthHeaders,
) -> None:
    response = await client.get(
        "/api/admin/email-templates/variables",
        headers=auth_headers,
    )

    assert response.status_code == 403


async def test_get_email_template_variables_not_authorized(
    client: AsyncClient,
) -> None:
    response = await client.get("/api/admin/email-templates/variables")

    assert response.status_code == 401
