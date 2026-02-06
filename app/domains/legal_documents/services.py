import os
from abc import ABC, abstractmethod
from typing import Annotated

from fastapi import Depends, UploadFile

from app.core.config import BASE_DIR, settings
from app.core.utils.save_file import save_file
from app.domains.legal_documents.types import LegalDocument


class LegalDocumentsServiceBase(ABC):
    def __init__(self, document: LegalDocument):
        self.document = document

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
        saved_path = await save_file(file, self.document.storage_path, filename=self.document.filename)
        return saved_path.as_posix()

    async def delete(self) -> None:
        filepath = BASE_DIR / self.document.storage_path / self.document.filename
        if filepath.exists():
            os.remove(filepath)

    async def get_path(self) -> str | None:
        filepath = BASE_DIR / self.document.storage_path / self.document.filename
        if filepath.exists():
            return (self.document.storage_path / self.document.filename).as_posix()
        return None


# --- Bylaws Specific Configuration ---

def get_bylaws_document() -> LegalDocument:
    return LegalDocument(
        filename="bylaws.pdf",
        storage_path=settings.BYLAWS_PATH
    )


def get_bylaws_service(
    document: Annotated[LegalDocument, Depends(get_bylaws_document)]
) -> LegalDocumentsServicePublic:
    return LegalDocumentsServicePublic(document)


BylawsServiceDep = Annotated[LegalDocumentsServiceBase, Depends(get_bylaws_service)]
BylawsPublicServiceDep = Annotated[LegalDocumentsServicePublic, Depends(get_bylaws_service)]
