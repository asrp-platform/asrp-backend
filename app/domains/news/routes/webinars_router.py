from typing import Annotated

from fastapi import APIRouter, Depends

from app.core.common.request_params import OrderingParamsDep, PaginationParamsDep
from app.core.common.responses import NotAuthorizedResponses, PaginatedResponse
from app.domains.news.filters import WebinarFilters
from app.domains.news.schemas import UserWebinarSchema
from app.domains.news.services import WebinarServiceDep
from app.domains.shared.deps import CurrentUserDep, OptionalCurrentUserDep


router = APIRouter(prefix="/webinars", tags=["Webinars"])


@router.get("", response_model_exclude_none=True)
async def get_webinars_paginated_counted(
    service: WebinarServiceDep,
    current_user: OptionalCurrentUserDep,
    params: PaginationParamsDep,
    ordering: OrderingParamsDep = None,
    filters: Annotated[WebinarFilters, Depends()] = None,
) -> PaginatedResponse[UserWebinarSchema]:
    data, count = await service.get_user_webinars_paginated_counted(
        user_id=current_user.id if current_user is not None else None,
        order_by=ordering,
        filters=filters.model_dump(exclude_none=True),
        limit=params["limit"],
        offset=params["offset"],
    )
    return PaginatedResponse(
        count=count,
        data=data,
        page=params["page"],
        page_size=params["page_size"],
    )


class RegisterForWebinarResponses(NotAuthorizedResponses):
    WEBINAR_NOT_FOUND = 404, "Webinar with provided slug not found"
    USER_NOT_FOUND = 404, "User with provided ID not found"
    MEMBERSHIP_REQUIRED = 403, "Active membership is required to register for this webinar"


@router.post(
    "/{webinar_slug}/registration",
    responses=RegisterForWebinarResponses.responses,
    status_code=201,
)
async def register_for_webinar(
    webinar_slug: str,
    current_user: CurrentUserDep,
    service: WebinarServiceDep,
) -> dict[str, str]:
    await service.register_for_webinar(webinar_slug, current_user.id)
    return {"status": "Successfully registered for the webinar"}
