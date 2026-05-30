from typing import Annotated

from fastapi import Depends

from app.domains.legal_documents.schemas import SponsorSchema
from app.domains.legal_documents.services import SponsorsService, SponsorsServiceDep


class GetSponsorsUseCase:
    def __init__(self, service: SponsorsService):
        self.__service = service

    async def execute(self) -> list[SponsorSchema]:
        items = await self.__service.get_all()
        return [
            SponsorSchema(
                id=item.id,
                created_at=item.created_at,
                updated_at=item.updated_at,
                name=item.name,
                link=item.link,
                short_name=item.short_name,
                logo_url=await self.__service.key_to_url(item.logo_key),
            )
            for item in items
        ]


def get_use_case(service: SponsorsServiceDep) -> GetSponsorsUseCase:
    return GetSponsorsUseCase(service)


GetSponsorsUseCaseDep = Annotated[GetSponsorsUseCase, Depends(get_use_case)]
