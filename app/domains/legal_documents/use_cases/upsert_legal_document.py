from typing import Annotated

from fastapi import Depends, File

from app.domains.legal_documents.services import LegalDocumentsServicePublic, get_bylaws_service


class UpsertLegalDocumentUseCase:
    def __init__(self, service):
        self.service = service

    async def execute(self, file: File) -> str:
        await self.service.upsert(file)
        return await self.service.get_path()


def get_upsert_legal_document_use_case(
    service: Annotated[LegalDocumentsServicePublic, Depends(get_bylaws_service)],
) -> UpsertLegalDocumentUseCase:
    return UpsertLegalDocumentUseCase(service)


UpsertLegalDocumentUseCaseDep = Annotated[UpsertLegalDocumentUseCase, Depends(get_upsert_legal_document_use_case)]
