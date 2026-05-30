from unittest.mock import AsyncMock

import pytest
from faker import Faker

from app.domains.legal_documents.models import Sponsor
from app.domains.shared.transaction_managers import TransactionManager


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


@pytest.fixture(scope="function")
def sponsor_data(faker: Faker) -> dict:
    return {
        "name": faker.company(),
        "short_name": faker.company_suffix(),
        "logo_url": f"http://localhost:9000/uploads/sponsors/{faker.file_name(extension='png')}",
        "link": faker.url(),
    }


@pytest.fixture(scope="function")
async def sponsor_db(
    test_transaction_manager: TransactionManager,
    sponsor_data: dict,
) -> Sponsor:
    from app.core.storage.storage_factory import get_file_storage
    file_storage = get_file_storage()

    data = sponsor_data.copy()
    if "logo_url" in data:
        # Extract key from URL
        url = data.pop("logo_url")
        path = url.split("/uploads/")[-1] if "/uploads/" in url else url.split("/")[-1]
        data["logo_key"] = path

        # Upload dummy content to make check_file_exists pass
        await file_storage.upload_file(object_key=path, file_content=b"fake")

    async with test_transaction_manager:
        return await test_transaction_manager.sponsor_repository.create(**data)
