from typing import Annotated

from fastapi import Depends

from app.domains.legal_documents.services import (
    LegalDocumentsService,
    get_submission_guidelines_service,
)
from app.domains.shared.types import FileData


class UpsertSubmissionGuidelinesUseCase:
    def __init__(self, service: LegalDocumentsService):
        self.service = service

    async def execute(self, file_data: FileData) -> str:
        await self.service.upsert(file_data)
        return await self.service.get_url()


def get_upsert_submission_guidelines_use_case(
    service: Annotated[LegalDocumentsService, Depends(get_submission_guidelines_service)],
) -> UpsertSubmissionGuidelinesUseCase:
    return UpsertSubmissionGuidelinesUseCase(service)


UpsertSubmissionGuidelinesUseCaseDep = Annotated[
    UpsertSubmissionGuidelinesUseCase,
    Depends(get_upsert_submission_guidelines_use_case),
]
