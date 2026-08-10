import pytest
from httpx import AsyncClient
from sqlalchemy import select

from app.domains.emails.models import EmailTemplate
from app.domains.shared.transaction_managers import TransactionManager
from tests.fixtures.auth import AuthHeaders


pytestmark = pytest.mark.anyio


async def test_delete_email_template(
    client: AsyncClient,
    admin_auth_headers: AuthHeaders,
    admin_all_permissions,
    email_template_db: EmailTemplate,
    test_transaction_manager: TransactionManager,
) -> None:
    delete_response = await client.delete(
        f"/api/admin/email-templates/{email_template_db.id}",
        headers=admin_auth_headers,
    )
    assert delete_response.status_code == 204

    get_response = await client.get(
        f"/api/admin/email-templates/{email_template_db.id}",
        headers=admin_auth_headers,
    )
    assert get_response.status_code == 404

    async with (test_transaction_manager):
        stmt = select(EmailTemplate).filter_by(id=email_template_db.id)
        email_template = (await test_transaction_manager._session.execute(stmt)).scalars().first()

    assert email_template._deleted


async def test_delete_email_template_not_found(
    client: AsyncClient,
    admin_auth_headers: AuthHeaders,
    admin_all_permissions,
    email_template_db: EmailTemplate,
) -> None:
    response = await client.delete(
        "/api/admin/email-templates/99999999",
        headers=admin_auth_headers,
    )
    assert response.status_code == 404


async def test_delete_email_template_no_permissions(
    client: AsyncClient,
    admin_auth_headers: AuthHeaders,
    email_template_db: EmailTemplate,
) -> None:
    response = await client.delete(
        f"/api/admin/email-templates/{email_template_db.id}",
        headers=admin_auth_headers,
    )

    assert response.status_code == 403


async def test_delete_email_template_not_authorized(
    client: AsyncClient,
    email_template_db: EmailTemplate,
) -> None:
    response = await client.delete(f"/api/admin/email-templates/{email_template_db.id}")

    assert response.status_code == 401


async def test_delete_email_template_by_user(
    client: AsyncClient,
    auth_headers: AuthHeaders,
    email_template_db: EmailTemplate,
) -> None:
    response = await client.delete(
        f"/api/admin/email-templates/{email_template_db.id}",
        headers=auth_headers,
    )

    assert response.status_code == 403
