
import pytest
from httpx import AsyncClient

from app.domains.emails.models import EmailTemplate
from tests.fixtures.auth import AuthHeaders


pytestmark = pytest.mark.anyio


async def test_update_email_template(
    client: AsyncClient,
    admin_auth_headers: AuthHeaders,
    admin_all_permissions,
    email_template_db: EmailTemplate
) -> None:
    update_data = {"name": "updated name"}

    response = await client.patch(
        f"/api/admin/email-templates/{email_template_db.id}",
        headers=admin_auth_headers,
        json=update_data,
    )

    assert response.status_code == 200

    assert response.json().get("id") == email_template_db.id
    assert response.json().get("name") == "updated name"


async def test_update_email_template_not_found(
    client: AsyncClient,
    admin_auth_headers: AuthHeaders,
    admin_all_permissions,
    email_template_db: EmailTemplate
) -> None:
    update_data = {"name": "updated name"}

    response = await client.patch(
        "/api/admin/email-templates/999999999",
        headers=admin_auth_headers,
        json=update_data,
    )

    assert response.status_code == 404


async def test_update_email_template_no_permissions(
    client: AsyncClient,
    admin_auth_headers: AuthHeaders,
    email_template_db: EmailTemplate
) -> None:
    update_data = {"name": "updated name"}

    response = await client.patch(
        f"/api/admin/email-templates/{email_template_db.id}",
        headers=admin_auth_headers,
        json=update_data,
    )

    assert response.status_code == 403


async def test_update_email_template_by_user(
    client: AsyncClient,
    auth_headers: AuthHeaders,
    email_template_db: EmailTemplate
) -> None:
    update_data = {"name": "updated name"}

    response = await client.patch(
        f"/api/admin/email-templates/{email_template_db.id}",
        headers=auth_headers,
        json=update_data,
    )

    assert response.status_code == 403


async def test_update_email_template_not_authorized(
    client: AsyncClient,
    email_template_db: EmailTemplate
) -> None:
    update_data = {"name": "updated name"}

    response = await client.patch(
        f"/api/admin/email-templates/{email_template_db.id}",
        json=update_data,
    )

    assert response.status_code == 401


async def test_update_email_template_without_editor_state(
    client: AsyncClient,
    admin_auth_headers: AuthHeaders,
    admin_all_permissions,
    email_template_db: EmailTemplate,
) -> None:
    update_data = {"name": "updated name", "html": "<h1>Oshibka</h1>"}

    response = await client.patch(
        f"/api/admin/email-templates/{email_template_db.id}",
        headers=admin_auth_headers,
        json=update_data,
    )

    assert response.status_code == 422


async def test_update_email_template_without_html(
    client: AsyncClient,
    admin_auth_headers: AuthHeaders,
    admin_all_permissions,
    email_template_db: EmailTemplate,
) -> None:
    update_data = {"name": "updated name", "editor_state": {}}

    response = await client.patch(
        f"/api/admin/email-templates/{email_template_db.id}",
        headers=admin_auth_headers,
        json=update_data,
    )

    assert response.status_code == 422
