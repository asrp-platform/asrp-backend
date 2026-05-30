from uuid import UUID

import pytest
from httpx import AsyncClient

from app.domains.legal_documents.models import Sponsor
from tests.fixtures.auth import AuthHeaders

pytestmark = pytest.mark.anyio


async def test_admin_get_sponsors_success(
    client: AsyncClient,
    admin_auth_headers: AuthHeaders,
    admin_all_permissions,
    sponsor_db: Sponsor,
) -> None:
    response = await client.get("/api/admin/legal-documents/sponsors", headers=admin_auth_headers)

    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1
    assert any(s["id"] == sponsor_db.id for s in data)


async def test_admin_create_sponsor_success(
    client: AsyncClient,
    admin_auth_headers: AuthHeaders,
    admin_all_permissions,
    sponsor_data: dict,
) -> None:
    response = await client.post(
        "/api/admin/legal-documents/sponsors",
        headers=admin_auth_headers,
        json=sponsor_data,
    )

    assert response.status_code == 201
    assert response.json()["name"] == sponsor_data["name"]


async def test_admin_update_sponsor_success(
    client: AsyncClient,
    admin_auth_headers: AuthHeaders,
    admin_all_permissions,
    sponsor_db: Sponsor,
) -> None:
    update_data = {"name": "Updated Sponsor Name"}
    response = await client.patch(
        f"/api/admin/legal-documents/sponsors/{sponsor_db.id}",
        headers=admin_auth_headers,
        json=update_data,
    )

    assert response.status_code == 200
    assert response.json()["name"] == update_data["name"]


async def test_admin_delete_sponsor_success(
    client: AsyncClient,
    admin_auth_headers: AuthHeaders,
    admin_all_permissions,
    sponsor_db: Sponsor,
) -> None:
    response = await client.delete(
        f"/api/admin/legal-documents/sponsors/{sponsor_db.id}",
        headers=admin_auth_headers,
    )

    assert response.status_code == 204

    # Verify it's gone from the list
    list_response = await client.get("/api/admin/legal-documents/sponsors", headers=admin_auth_headers)
    assert list_response.status_code == 200
    assert all(s["id"] != sponsor_db.id for s in list_response.json())


async def test_admin_upload_sponsor_logo_success(
    client: AsyncClient,
    admin_auth_headers: AuthHeaders,
    admin_all_permissions,
    spy_file_storage,
) -> None:
    files = {"file": ("logo.png", b"fake image content", "image/png")}
    response = await client.put(
        "/api/admin/legal-documents/sponsors/logos",
        headers=admin_auth_headers,
        files=files,
    )

    assert response.status_code == 200
    data = response.json()
    assert "url" in data
    assert data["url"].startswith("http")

    object_key = spy_file_storage["upload_file"].call_args.kwargs["object_key"]
    prefix, stored_name = object_key.split("/", 1)
    file_uuid, original_name = stored_name.split("_", 1)

    assert prefix == "sponsors"
    UUID(file_uuid)
    assert original_name == "logo.png"


async def test_admin_create_sponsor_no_permissions(
    client: AsyncClient,
    admin_auth_headers: AuthHeaders,
    sponsor_data: dict,
) -> None:
    response = await client.post(
        "/api/admin/legal-documents/sponsors",
        headers=admin_auth_headers,
        json=sponsor_data,
    )

    assert response.status_code == 403
