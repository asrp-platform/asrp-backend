from typing import Annotated

from fastapi import Depends

from app.core.common.exceptions import InvalidMimeTypeError
from app.core.storage.base_storage import BaseFileStorage
from app.core.storage.storage_factory import get_file_storage
from app.domains.legal_documents.types import LegalDocument
from app.domains.shared.types import FileData


class LegalDocumentsService:
    def __init__(self, document: LegalDocument, file_storage: BaseFileStorage):
        self.document = document
        self.file_storage = file_storage

    async def upsert(self, file_data: FileData) -> None:
        if file_data.content_type != self.document.mime_type:
            raise InvalidMimeTypeError

        await self.file_storage.upload_file(self.document.filename, file_content=file_data.content)

    async def delete(self) -> None:
        await self.file_storage.delete_file(self.document.filename)

    async def get_url(self) -> str | None:
        return await self.file_storage.get_file_url(self.document.filename)


def get_bylaws_document() -> LegalDocument:
    return LegalDocument(
        filename="legal_documents/bylaws.pdf",
        mime_type="application/pdf",
    )


def get_bylaws_service(
    document: Annotated[LegalDocument, Depends(get_bylaws_document)],
    file_storage: Annotated[BaseFileStorage, Depends(get_file_storage)],
) -> LegalDocumentsService:
    return LegalDocumentsService(document, file_storage)


BylawsServiceDep = Annotated[LegalDocumentsService, Depends(get_bylaws_service)]
