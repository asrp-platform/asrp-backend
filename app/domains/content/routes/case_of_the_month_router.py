from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi_exception_responses import Responses

from app.core.common.request_params import OrderingParamsDep, PaginationParamsDep
from app.core.common.responses import PaginatedResponse
from app.domains.content.filters import CaseOfTheMonthFilter
from app.domains.content.schemas import CaseOfTheMonthSchema, CaseTagSchema
from app.domains.content.use_cases import (
    GetCaseOfTheMonthListUseCaseDep,
    GetCaseOfTheMonthUseCaseDep,
    GetCaseTagsUseCaseDep,
    GetCaseTagUseCaseDep,
)


router = APIRouter(prefix="/case-of-the-month", tags=["Case of the Month"])


class CaseTagResponses(Responses):
    CASE_TAG_NOT_FOUND = 404, "Case tag with provided ID not found"
    CASE_TAG_ALREADY_EXISTS = 409, "Case tag with provided name already exists"


class CaseOfTheMonthResponses(Responses):
    CASE_NOT_FOUND = 404, "Case of the month with provided ID not found"
    INVALID_SORTER_FIELD = 400, "Invalid sorter field"


@router.get(
    "/cases",
    summary="Get a paginated list of case of the month articles",
    status_code=200,
    responses=CaseOfTheMonthResponses.responses,
)
async def get_cases(
    use_case: GetCaseOfTheMonthListUseCaseDep,
    params: PaginationParamsDep,
    ordering: OrderingParamsDep = None,
    filters: Annotated[CaseOfTheMonthFilter, Depends()] = None,
) -> PaginatedResponse[CaseOfTheMonthSchema]:
    data, count = await use_case.execute(
        limit=params["limit"],
        offset=params["offset"],
        order_by=ordering,
        filters=filters.model_dump(exclude_none=True) if filters else {},
    )
    return PaginatedResponse(
        count=count,
        data=data,
        page=params["page"],
        page_size=params["page_size"],
    )


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


@router.get(
    "/cases/{case_slug}",
    summary="Get a case of the month article by slug",
    status_code=200,
    responses=CaseOfTheMonthResponses.responses,
)
async def get_case(
    case_slug: str,
    use_case: GetCaseOfTheMonthUseCaseDep,
) -> CaseOfTheMonthSchema:
    return await use_case.execute_by_slug(case_slug)
