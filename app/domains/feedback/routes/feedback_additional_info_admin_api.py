from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi_exception_responses import Responses

from app.core.common.request_params import PaginationParamsDep
from app.core.common.responses import PaginatedResponse, PermissionsResponses
from app.domains.feedback.filters import FeedbackInterestsFilter
from app.domains.feedback.schemas import FeedbackInterestResponseSchema, HearAboutStatsResponseSchema
from app.domains.feedback.use_cases import GetHearAboutStatsUseCaseDep, GetInterestsUseCaseDep
from app.domains.shared.deps import AdminPermissionsDep, get_admin_user


router = APIRouter(
    prefix="/feedback-additional-info",
    tags=["Admin: Feedback Additional Info"],
    dependencies=[Depends(get_admin_user)],
)


class GetInterestsResponses(Responses):
    INVALID_DATE_RANGE = 422, "date_from must be less than or equal to date_to"


class GetHearAboutStatsResponses(PermissionsResponses):
    INVALID_DATE_RANGE = 422, "date_from must be less than or equal to date_to"


class GetInterestsListResponses(PermissionsResponses, GetInterestsResponses):
    pass


@router.get(
    "/hear-about-stats",
    summary="Get hear about ASRP statistics",
    description="Returns aggregated counts and percentages for how users learned about ASRP. "
    "Unknown legacy values are grouped into 'Other'.",
    responses=GetHearAboutStatsResponses.responses,
    status_code=200,
)
async def get_hear_about_stats(
    permissions: AdminPermissionsDep,
    use_case: GetHearAboutStatsUseCaseDep,
    date_from: Annotated[date | None, Query()] = None,
    date_to: Annotated[date | None, Query()] = None,
) -> HearAboutStatsResponseSchema:
    if date_from and date_to and date_from > date_to:
        raise HTTPException(status_code=422, detail="date_from must be less than or equal to date_to")
    return await use_case.execute(
        permissions=permissions,
        date_from=date_from,
        date_to=date_to,
    )


@router.get(
    "/interests",
    summary="Get paginated list of user interests",
    description="Returns paginated records with non-null interest descriptions and optional Telegram usernames.",
    responses=GetInterestsListResponses.responses,
    status_code=200,
)
async def get_interests(
    permissions: AdminPermissionsDep,
    use_case: GetInterestsUseCaseDep,
    params: PaginationParamsDep,
    filters: Annotated[FeedbackInterestsFilter, Depends()] = None,
    date_from: Annotated[date | None, Query()] = None,
    date_to: Annotated[date | None, Query()] = None,
) -> PaginatedResponse[FeedbackInterestResponseSchema]:
    if date_from and date_to and date_from > date_to:
        raise HTTPException(status_code=422, detail="date_from must be less than or equal to date_to")
    filter_data = filters.model_dump(exclude_none=True) if filters else {}
    filter_data["date_from"] = date_from
    filter_data["date_to"] = date_to

    data, count = await use_case.execute(
        permissions=permissions,
        limit=params["limit"],
        offset=params["offset"],
        search=filter_data.get("search"),
        has_telegram=filter_data.get("has_telegram"),
        date_from=filter_data.get("date_from"),
        date_to=filter_data.get("date_to"),
    )

    return PaginatedResponse(
        count=count,
        data=data,
        page=params["page"],
        page_size=params["page_size"],
    )
