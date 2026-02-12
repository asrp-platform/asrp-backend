from unittest.mock import AsyncMock

import pytest
from faker import Faker
from httpx import AsyncClient

from app.core.config import settings
from app.domains.legal_documents.routes.api import BylawsResponses
from tests.fixtures.auth import AuthHeaders

pytestmark = pytest.mark.anyio


@pytest.fixture(scope="function")
def mock_service() -> AsyncMock:
    return AsyncMock()


@pytest.fixture(scope="function", autouse=True)
def override_bylaws_service(mock_service: AsyncMock) -> None:
    from app.domains.legal_documents.services import get_bylaws_service
    from app.main import app

    app.dependency_overrides[get_bylaws_service] = lambda: mock_service
    yield
    app.dependency_overrides.clear()


async def test_get_bylaws_success(
    client: AsyncClient,
    mock_service: AsyncMock,
) -> None:
    expected_path = (settings.BYLAWS_PATH / "bylaws.pdf").as_posix()
    mock_service.get_path.return_value = expected_path

    response = await client.get("/api/legal-documents/bylaws")

    assert response.status_code == 200
    assert response.json() == {"url": expected_path}


async def test_get_bylaws_not_found(
    client: AsyncClient,
    mock_service: AsyncMock,
) -> None:
    mock_service.get_path.return_value = None

    response = await client.get("/api/legal-documents/bylaws")

    assert response.status_code == 404
    assert response.json()["detail"] == BylawsResponses.NOT_FOUND.detail  # type: ignore[attr-defined]


async def test_upsert_bylaws_success(
    client: AsyncClient,
    mock_service: AsyncMock,
    admin_auth_headers: AuthHeaders,
    admin_all_permissions,
    faker: Faker,
) -> None:
    expected_path = (settings.BYLAWS_PATH / "bylaws.pdf").as_posix()
    files = {"file": ("bylaws.pdf", faker.binary(length=12), "application/pdf")}
    mock_service.upsert.return_value = expected_path

    response = await client.put("/api/admin/legal-documents/bylaws", files=files, headers=admin_auth_headers)

    assert response.status_code == 200
    assert response.json() == {"url": expected_path}


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
    mock_service: AsyncMock,
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
) -> None:
    response = await client.delete("/api/admin/legal-documents/bylaws", headers=admin_auth_headers)

    assert response.status_code == 204
    mock_service.delete.assert_called_once()
