from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from fastapi_exception_responses import Responses

from app.core.common.request_params import PaginationParamsDep
from app.core.common.responses import PaginatedResponse, PermissionsResponses
from app.domains.feedback.filters import FeedbackInterestsFilter
from app.domains.feedback.schemas import FeedbackInterestResponseSchema, HearAboutStatsResponseSchema
from app.domains.feedback.use_cases.get_hear_about_stats import GetHearAboutStatsUseCaseDep
from app.domains.feedback.use_cases.get_interests import GetInterestsUseCaseDep
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
)
async def get_hear_about_stats(
    permissions: AdminPermissionsDep,
    use_case: GetHearAboutStatsUseCaseDep,
    date_from: Annotated[
        date | None,
        Query(description="Include records created on or after this date (inclusive), format YYYY-MM-DD."),
    ] = None,
    date_to: Annotated[
        date | None,
        Query(description="Include records created on or before this date (inclusive), format YYYY-MM-DD."),
    ] = None,
) -> HearAboutStatsResponseSchema:
    if date_from and date_to and date_from > date_to:
        raise GetHearAboutStatsResponses.INVALID_DATE_RANGE

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
)
async def get_interests(
    permissions: AdminPermissionsDep,
    use_case: GetInterestsUseCaseDep,
    params: PaginationParamsDep,
    filters: Annotated[FeedbackInterestsFilter, Depends()] = None,
) -> PaginatedResponse[FeedbackInterestResponseSchema]:
    filter_data = filters.model_dump(exclude_none=True) if filters else {}

    if filters and filters.date_from and filters.date_to and filters.date_from > filters.date_to:
        raise GetInterestsResponses.INVALID_DATE_RANGE

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
