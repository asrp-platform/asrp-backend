import pytest
from httpx import AsyncClient
from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.emails.models import EmailTemplate
from tests.fixtures.auth import AuthHeaders


pytestmark = pytest.mark.anyio


async def test_get_email_template(
    client: AsyncClient,
    admin_auth_headers: AuthHeaders,
    admin_all_permissions,
    email_template_db: EmailTemplate,
) -> None:
    response = await client.get(
        f"/api/admin/email-templates/{email_template_db.id}",
        headers=admin_auth_headers,
    )

    assert response.status_code == 200

    assert response.json().get("id") == email_template_db.id
    assert response.json().get("name") == email_template_db.name


async def test_get_email_template_no_permissions(
    client: AsyncClient,
    admin_auth_headers: AuthHeaders,
    email_template_db: EmailTemplate,
) -> None:
    response = await client.get(
        f"/api/admin/email-templates/{email_template_db.id}",
        headers=admin_auth_headers,
    )

    assert response.status_code == 403


async def test_get_email_template_by_user(
    client: AsyncClient,
    auth_headers: AuthHeaders,
    email_template_db: EmailTemplate,
) -> None:
    response = await client.get(
        f"/api/admin/email-templates/{email_template_db.id}",
        headers=auth_headers,
    )

    assert response.status_code == 403


async def test_get_email_template_not_authorized(
    client: AsyncClient,
    email_template_db: EmailTemplate,
) -> None:
    response = await client.get(f"/api/admin/email-templates/{email_template_db.id}")

    assert response.status_code == 401


async def test_get_email_template_not_found(
    client: AsyncClient,
    admin_auth_headers: AuthHeaders,
    admin_all_permissions,
    email_template_db: EmailTemplate,
) -> None:
    response = await client.get(
        "/api/admin/email-templates/999999999",
        headers=admin_auth_headers
    )

    assert response.status_code == 404


async def test_get_email_templates(
    client: AsyncClient,
    admin_auth_headers: AuthHeaders,
    admin_all_permissions,
    email_template_db: EmailTemplate,
) -> None:
    response = await client.get(
        "/api/admin/email-templates",
        headers=admin_auth_headers,
    )

    assert response.status_code == 200

    data = response.json()

    assert isinstance(data, list)
    assert len(data) >= 1


async def test_get_email_templates_empty(
    client: AsyncClient,
    test_session: AsyncSession,
    admin_auth_headers: AuthHeaders,
    admin_all_permissions,
) -> None:
    await test_session.execute(delete(EmailTemplate))
    await test_session.commit()

    response = await client.get(
        "/api/admin/email-templates",
        headers=admin_auth_headers,
    )

    assert response.status_code == 200

    data = response.json()

    assert isinstance(data, list)
    assert len(data) == 0


async def test_get_email_templates_no_permissions(
    client: AsyncClient,
    admin_auth_headers: AuthHeaders,
) -> None:
    response = await client.get(
        "/api/admin/email-templates",
        headers=admin_auth_headers,
    )

    assert response.status_code == 403


async def test_get_email_templates_by_user(
    client: AsyncClient,
    auth_headers: AuthHeaders,
    email_template_db: EmailTemplate,
) -> None:
    response = await client.get(
        "/api/admin/email-templates",
        headers=auth_headers,
    )

    assert response.status_code == 403


async def test_get_email_templates_not_authorized(
    client: AsyncClient,
    email_template_db: EmailTemplate,
) -> None:
    response = await client.get("/api/admin/email-templates")

    assert response.status_code == 401
