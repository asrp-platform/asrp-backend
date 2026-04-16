from typing import Annotated

from fastapi import Depends

from app.domains.legal_documents.services import LegalDocumentsService, get_bylaws_service
from app.domains.shared.types import FileData


class UpsertBylawsUseCase:
    def __init__(self, service):
        self.service = service

    async def execute(self, file_data: FileData) -> str:
        await self.service.upsert(file_data)
        return await self.service.get_url()


def get_upsert_legal_document_use_case(
    service: Annotated[LegalDocumentsService, Depends(get_bylaws_service)],
) -> UpsertBylawsUseCase:
    return UpsertBylawsUseCase(service)


UpsertBylawsUseCaseDep = Annotated[UpsertBylawsUseCase, Depends(get_upsert_legal_document_use_case)]
