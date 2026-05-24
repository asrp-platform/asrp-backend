from typing import Annotated

from fastapi import Depends

from app.core.utils.permissions import check_permissions
from app.domains.legal_documents.schemas import SponsorSchema
from app.domains.legal_documents.services import SponsorsService, SponsorsServiceDep


class CreateSponsorUseCase:
    def __init__(self, service: SponsorsService):
        self.__service = service

    async def execute(self, permissions, **kwargs) -> SponsorSchema:
        check_permissions("legal_documents.update", permissions)
        logo_key = self.__service.url_to_key(kwargs.pop("logo_url", None))
        item = await self.__service.create(logo_key=logo_key, **kwargs)
        return SponsorSchema(
            id=item.id,
            created_at=item.created_at,
            updated_at=item.updated_at,
            name=item.name,
            link=item.link,
            short_name=item.short_name,
            logo_url=await self.__service.key_to_url(item.logo_key),
        )


def get_use_case(service: SponsorsServiceDep) -> CreateSponsorUseCase:
    return CreateSponsorUseCase(service)


CreateSponsorUseCaseDep = Annotated[CreateSponsorUseCase, Depends(get_use_case)]
