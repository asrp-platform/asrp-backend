from fastapi import APIRouter
from fastapi_exception_responses import Responses

from app.domains.content.schemas import CaseTagSchema
from app.domains.content.use_cases import GetCaseTagsUseCaseDep, GetCaseTagUseCaseDep


router = APIRouter(prefix="/case-of-the-month", tags=["Case of the Month"])


class CaseTagResponses(Responses):
    CASE_TAG_NOT_FOUND = 404, "Case tag with provided ID not found"
    CASE_TAG_ALREADY_EXISTS = 409, "Case tag with provided name already exists"


@router.get(
    "/tags",
    summary="Get all case of the month tags",
    status_code=200,
    responses=CaseTagResponses.responses,
)
async def get_case_tags(use_case: GetCaseTagsUseCaseDep) -> list[CaseTagSchema]:
    return await use_case.execute()


@router.get(
    "/tags/{tag_id}",
    summary="Get a case of the month tag by ID",
    status_code=200,
    responses=CaseTagResponses.responses,
)
async def get_case_tag(tag_id: int, use_case: GetCaseTagUseCaseDep) -> CaseTagSchema:
    return await use_case.execute(tag_id)
