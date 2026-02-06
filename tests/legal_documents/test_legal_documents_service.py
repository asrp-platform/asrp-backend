from io import BytesIO
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest
from faker import Faker
from fastapi import UploadFile

from app.domains.legal_documents.services import LegalDocumentsServicePublic
from app.domains.legal_documents.types import LegalDocument

pytestmark = pytest.mark.anyio


@pytest.fixture(scope="function")
def mock_document(faker) -> LegalDocument:
    return LegalDocument(filename=faker.file_name(extension="pdf"), storage_path=Path(faker.word()))


@pytest.fixture(scope="function")
def service(mock_document: LegalDocument) -> LegalDocumentsServicePublic:
    return LegalDocumentsServicePublic(mock_document)


async def test_upsert(
    service: LegalDocumentsServicePublic,
    mock_document: LegalDocument,
    faker: Faker,
) -> None:
    expected_path = mock_document.storage_path / mock_document.filename
    mock_save = AsyncMock(return_value=expected_path)

    with patch("app.domains.legal_documents.services.save_file", mock_save):
        file = UploadFile(file=BytesIO(faker.binary(length=12)), filename=faker.file_name(extension="pdf"))
        path = await service.upsert(file)

        assert path == expected_path.as_posix()
        mock_save.assert_called_once_with(file, mock_document.storage_path, filename=mock_document.filename)


async def test_get_path_exists(
    service: LegalDocumentsServicePublic,
    mock_document: LegalDocument,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    faker: Faker,
) -> None:
    monkeypatch.setattr("app.domains.legal_documents.services.BASE_DIR", tmp_path)

    full_path = tmp_path / mock_document.storage_path / mock_document.filename
    full_path.parent.mkdir(parents=True, exist_ok=True)
    full_path.write_bytes(faker.binary(length=12))

    path = await service.get_path()
    assert path == (mock_document.storage_path / mock_document.filename).as_posix()


async def test_get_path_not_exists(
    service: LegalDocumentsServicePublic,
    mock_document: LegalDocument,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr("app.domains.legal_documents.services.BASE_DIR", tmp_path)

    path = await service.get_path()
    assert path is None


async def test_delete(
    service: LegalDocumentsServicePublic,
    mock_document: LegalDocument,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    faker: Faker,
) -> None:
    monkeypatch.setattr("app.domains.legal_documents.services.BASE_DIR", tmp_path)

    full_path = tmp_path / mock_document.storage_path / mock_document.filename
    full_path.parent.mkdir(parents=True, exist_ok=True)
    full_path.write_bytes(faker.binary(length=12))

    assert full_path.exists()

    await service.delete()

    assert not full_path.exists()
