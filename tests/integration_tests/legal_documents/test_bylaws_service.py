from unittest.mock import AsyncMock

import pytest

from app.domains.legal_documents.services import LegalDocumentsService
from app.domains.legal_documents.types import LegalDocument
from app.domains.shared.types import FileData


pytestmark = pytest.mark.anyio


async def test_upsert_bylaws_uploads_pdf_for_inline_viewing() -> None:
    storage = AsyncMock()
    service = LegalDocumentsService(
        document=LegalDocument(filename="legal_documents/bylaws.pdf", mime_type="application/pdf"),
        file_storage=storage,
    )

    await service.upsert(FileData(content=b"pdf", content_type="application/pdf", filename="bylaws.pdf"))

    storage.upload_file.assert_awaited_once_with(
        "legal_documents/bylaws.pdf",
        file_content=b"pdf",
        content_type="application/pdf",
        content_disposition="inline",
    )


async def test_get_bylaws_url_requests_inline_pdf_response() -> None:
    storage = AsyncMock()
    storage.get_file_url.return_value = "https://storage.example/bylaws.pdf"
    service = LegalDocumentsService(
        document=LegalDocument(filename="legal_documents/bylaws.pdf", mime_type="application/pdf"),
        file_storage=storage,
    )

    url = await service.get_url()

    assert url == "https://storage.example/bylaws.pdf"
    storage.get_file_url.assert_awaited_once_with(
        "legal_documents/bylaws.pdf",
        response_content_type="application/pdf",
        response_content_disposition="inline",
    )
