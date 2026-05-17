from fastapi import APIRouter
from fastapi_exception_responses import Responses

from app.domains.legal_documents.schemas import SponsorSchema, ViewLegalDocumentSchema
from app.domains.legal_documents.services import BylawsServiceDep
from app.domains.legal_documents.use_cases.get_sponsors import GetSponsorsUseCaseDep

router = APIRouter(prefix="/legal-documents", tags=["Legal Documents"])


class BylawsResponses(Responses):
    NOT_FOUND = 404, "Bylaws document not found"


@router.get(
    "/bylaws",
    summary="Get link to bylaws document",
    responses=BylawsResponses.responses,
)
async def get_bylaws(
    service: BylawsServiceDep,
) -> ViewLegalDocumentSchema:
    url = await service.get_url()
    if not url:
        raise BylawsResponses.NOT_FOUND
    return ViewLegalDocumentSchema(url=url)


class GetSponsorsResponses(Responses):
    pass


@router.get(
    "/sponsors",
    summary="Get list of sponsors",
    responses=GetSponsorsResponses.responses,
)
async def get_sponsors(
    use_case: GetSponsorsUseCaseDep,
) -> list[SponsorSchema]:
    return await use_case.execute()
