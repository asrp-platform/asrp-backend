from unittest.mock import AsyncMock

import pytest
from faker import Faker
from httpx import AsyncClient

from tests.fixtures.auth import AuthHeaders

pytestmark = pytest.mark.anyio


async def test_get_bylaws_success(
    client: AsyncClient,
    mock_service: AsyncMock,
    faker: Faker,
    override_bylaws_service,
) -> None:
    mock_service.get_url.return_value = faker.url()

    response = await client.get("/api/legal-documents/bylaws")

    assert response.status_code == 200


async def test_get_bylaws_not_found(
    client: AsyncClient,
    mock_service: AsyncMock,
) -> None:
    mock_service.get_url.return_value = None

    response = await client.get("/api/legal-documents/bylaws")

    assert response.status_code == 404


async def test_upsert_bylaws_success(
    client: AsyncClient,
    mock_service: AsyncMock,
    admin_auth_headers: AuthHeaders,
    admin_all_permissions,
    faker: Faker,
) -> None:
    files = {"file": ("bylaws.pdf", faker.binary(length=12), "application/pdf")}
    mock_service.get_url.return_value = faker.url()

    response = await client.put("/api/admin/legal-documents/bylaws", files=files, headers=admin_auth_headers)

    assert response.status_code == 200


async def test_upsert_bylaws_forbidden(
    client: AsyncClient,
    mock_service: AsyncMock,
    admin_auth_headers: AuthHeaders,
    faker: Faker,
) -> None:
    files = {"file": ("bylaws.pdf", faker.binary(length=12), "application/pdf")}

    response = await client.put("/api/admin/legal-documents/bylaws", files=files, headers=admin_auth_headers)

    assert response.status_code == 403


async def test_upsert_bylaws_invalid_type(
    client: AsyncClient,
    admin_auth_headers: AuthHeaders,
    admin_all_permissions,
    faker: Faker,
) -> None:
    files = {"file": ("bylaws.txt", faker.binary(length=12), "text/plain")}

    response = await client.put("/api/admin/legal-documents/bylaws", files=files, headers=admin_auth_headers)

    assert response.status_code == 415


async def test_delete_bylaws_success(
    client: AsyncClient,
    mock_service: AsyncMock,
    admin_auth_headers: AuthHeaders,
    admin_all_permissions,
    override_bylaws_service,
) -> None:
    response = await client.delete("/api/admin/legal-documents/bylaws", headers=admin_auth_headers)

    assert response.status_code == 204
    mock_service.delete.assert_called_once()
