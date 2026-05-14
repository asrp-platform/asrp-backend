from typing import Annotated

from fastapi import Depends

from app.core.utils.permissions import check_permissions
from app.domains.legal_documents.services import SponsorsService, SponsorsServiceDep


class DeleteSponsorUseCase:
    def __init__(self, service: SponsorsService):
        self.__service = service

    async def execute(self, permissions, sponsor_id: int) -> None:
        check_permissions("legal_documents.delete", permissions)
        await self.__service.delete(sponsor_id)


def get_use_case(service: SponsorsServiceDep) -> DeleteSponsorUseCase:
    return DeleteSponsorUseCase(service)


DeleteSponsorUseCaseDep = Annotated[DeleteSponsorUseCase, Depends(get_use_case)]
