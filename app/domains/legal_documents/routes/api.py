from fastapi import APIRouter
from fastapi_exception_responses import Responses

from app.domains.legal_documents.services import BylawsPublicServiceDep

router = APIRouter(prefix="/legal-documents", tags=["Legal Documents"])


class BylawsResponses(Responses):
    NOT_FOUND = 404, "Bylaws document not found"


@router.get(
    "/bylaws",
    summary="Get link to bylaws document",
    responses=BylawsResponses.responses,
)
async def get_bylaws(
    service: BylawsPublicServiceDep,
) -> dict:
    path = await service.get_path()
    if not path:
        raise BylawsResponses.NOT_FOUND
    return {"url": path}
