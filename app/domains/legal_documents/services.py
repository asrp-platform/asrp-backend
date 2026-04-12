from abc import ABC, abstractmethod
from typing import Annotated

from fastapi import Depends, UploadFile

from app.core.config import s3_storage, settings
from app.domains.legal_documents.types import LegalDocument


class LegalDocumentsServiceBase(ABC):
    def __init__(self, document: LegalDocument):
        self.document = document
        self.file_storage = s3_storage

    @abstractmethod
    async def upsert(self, file: UploadFile) -> str:
        """
        Saves or overwrites the legal document.
        Returns the relative path or URL to the file.
        """
        pass

    @abstractmethod
    async def delete(self) -> None:
        """
        Deletes the legal document if it exists.
        """
        pass

    @abstractmethod
    async def get_path(self) -> str | None:
        """
        Returns the relative path/URL to the legal document if it exists.
        """
        pass


class LegalDocumentsServicePublic(LegalDocumentsServiceBase):
    async def upsert(self, file: UploadFile) -> str:
        file = await file.read()
        await self.file_storage.upload_file(self.document.filename, file)

    async def delete(self) -> None:
        await self.file_storage.delete_object(self.document.filename)

    async def get_path(self) -> str | None:
        return await self.file_storage.get_presigned_object(self.document.filename)


# --- Bylaws Specific Configuration ---

def get_bylaws_document() -> LegalDocument:
    return LegalDocument(
        filename="legal_documents/bylaws.pdf",
        storage_path=settings.BYLAWS_PATH
    )


def get_bylaws_service(
    document: Annotated[LegalDocument, Depends(get_bylaws_document)]
) -> LegalDocumentsServicePublic:
    return LegalDocumentsServicePublic(document)


BylawsServiceDep = Annotated[LegalDocumentsServiceBase, Depends(get_bylaws_service)]
BylawsPublicServiceDep = Annotated[LegalDocumentsServicePublic, Depends(get_bylaws_service)]
