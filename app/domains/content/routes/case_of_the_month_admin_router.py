from fastapi import APIRouter
from fastapi_exception_responses import Responses

from app.domains.content.schemas import CaseTagSchema, CreateCaseTagSchema, UpdateCaseTagSchema
from app.domains.content.use_cases import (
    CreateCaseTagUseCaseDep,
    DeleteCaseTagUseCaseDep,
    GetCaseTagsUseCaseDep,
    GetCaseTagUseCaseDep,
    UpdateCaseTagUseCaseDep,
)


router = APIRouter(prefix="/case-of-the-month", tags=["Admin: Case of the Month"])


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


@router.post(
    "/tags",
    summary="Create a case of the month tag",
    status_code=201,
    responses=CaseTagResponses.responses,
)
async def create_case_tag(body: CreateCaseTagSchema, use_case: CreateCaseTagUseCaseDep) -> CaseTagSchema:
    return await use_case.execute(**body.model_dump())


@router.patch(
    "/tags/{tag_id}",
    summary="Update a case of the month tag",
    status_code=200,
    responses=CaseTagResponses.responses,
)
async def update_case_tag(
    tag_id: int,
    body: UpdateCaseTagSchema,
    use_case: UpdateCaseTagUseCaseDep,
) -> CaseTagSchema:
    return await use_case.execute(tag_id, body.model_dump(exclude_unset=True))


@router.delete(
    "/tags/{tag_id}",
    summary="Delete a case of the month tag",
    status_code=204,
    responses=CaseTagResponses.responses,
)
async def delete_case_tag(tag_id: int, use_case: DeleteCaseTagUseCaseDep) -> None:
    await use_case.execute(tag_id)
