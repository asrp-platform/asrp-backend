import pytest
from httpx import AsyncClient
from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.legal_documents.models import Sponsor

pytestmark = pytest.mark.anyio


async def test_get_sponsors_success(
    client: AsyncClient,
    sponsor_db: Sponsor,
) -> None:
    response = await client.get("/api/legal-documents/sponsors")

    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1
    assert any(s["id"] == sponsor_db.id for s in data)

    sponsor = next(s for s in data if s["id"] == sponsor_db.id)
    assert sponsor["logo_url"] is not None
    assert sponsor["logo_url"].startswith("http")


async def test_get_sponsors_empty(
    client: AsyncClient,
    test_session: AsyncSession,
) -> None:
    # Ensure clean state
    await test_session.execute(delete(Sponsor))
    await test_session.commit()

    # No sponsors created
    response = await client.get("/api/legal-documents/sponsors")

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 0
