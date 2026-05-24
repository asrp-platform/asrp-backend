from typing import Annotated

from fastapi import Depends

from app.domains.legal_documents.services import SponsorsService, SponsorsServiceDep
from app.domains.shared.types import FileData


class UploadSponsorLogoUseCase:
    def __init__(
        self,
        sponsors_service: SponsorsService,
    ):
        self.__sponsors_service = sponsors_service

    async def execute(self, file_data: FileData) -> str | None:
        """Uploads logo image and returns a presigned URL for immediate use."""
        object_key = await self.__sponsors_service.upload_logo(file_data)
        return await self.__sponsors_service.key_to_url(object_key)


def get_use_case(sponsors_service: SponsorsServiceDep) -> UploadSponsorLogoUseCase:
    return UploadSponsorLogoUseCase(sponsors_service)


UploadSponsorLogoUseCaseDep = Annotated[UploadSponsorLogoUseCase, Depends(get_use_case)]
