from unittest.mock import AsyncMock

import pytest


@pytest.fixture(scope="function")
def mock_service() -> AsyncMock:
    return AsyncMock()


@pytest.fixture(scope="function")
def override_bylaws_service(mock_service: AsyncMock) -> None:
    from app.domains.legal_documents.services import get_bylaws_service
    from app.main import app

    app.dependency_overrides[get_bylaws_service] = lambda: mock_service
    yield
    app.dependency_overrides.clear()
