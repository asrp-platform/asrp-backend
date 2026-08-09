from datetime import datetime, timezone
from typing import Annotated

from fastapi import APIRouter, Depends

from app.core.common.request_params import OrderingParamsDep, PaginationParamsDep
from app.core.common.responses import NotAuthorizedResponses, PaginatedResponse
from app.domains.memberships.models import UserMembership
from app.domains.memberships.utils import has_member_access
from app.domains.news.filters import WebinarFilters
from app.domains.news.models import Webinar
from app.domains.news.schemas import UserWebinarSchema, WebinarBaseSchema, WebinarPlaybackSchema
from app.domains.news.services import WebinarServiceDep
from app.domains.shared.deps import CurrentUserDep, OptionalCurrentUserDep


router = APIRouter(prefix="/webinars", tags=["Webinars"])


def serialize_user_webinar(
    webinar: Webinar,
    *,
    user_id: int | None,
    membership: UserMembership | None,
) -> UserWebinarSchema:
    is_registered = user_id is not None and any(user.id == user_id for user in webinar.registered_users)
    response = UserWebinarSchema.model_validate({
        **WebinarBaseSchema.model_validate(webinar, from_attributes=True).model_dump(),
        "is_registered": is_registered,
    })
    can_view_links = user_id is not None and (not webinar.member_only or has_member_access(membership))
    can_join = can_view_links and is_registered and webinar.starts_at <= datetime.now(timezone.utc) <= webinar.ends_at

    return response.model_copy(
        update={
            "join_link": response.join_link if can_join else None,
        }
    )


@router.get("", response_model_exclude_none=True)
async def get_webinars_paginated_counted(
    service: WebinarServiceDep,
    current_user: OptionalCurrentUserDep,
    params: PaginationParamsDep,
    ordering: OrderingParamsDep = None,
    filters: Annotated[WebinarFilters, Depends()] = None,
) -> PaginatedResponse[UserWebinarSchema]:
    webinars, count, membership = await service.get_user_webinars_paginated_counted(
        user_id=current_user.id if current_user is not None else None,
        order_by=ordering,
        filters=filters.model_dump(exclude_none=True),
        limit=params["limit"],
        offset=params["offset"],
    )
    data = [
        serialize_user_webinar(
            webinar,
            user_id=current_user.id if current_user is not None else None,
            membership=membership,
        )
        for webinar in webinars
    ]
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


class WebinarPlaybackResponses(NotAuthorizedResponses):
    WEBINAR_NOT_FOUND = 404, "Webinar with provided slug not found"
    MEMBERSHIP_REQUIRED = 403, "Active membership is required to view this webinar"


@router.get(
    "/{webinar_slug}/playback",
    responses=WebinarPlaybackResponses.responses,
)
async def get_webinar_playback(
    webinar_slug: str,
    current_user: CurrentUserDep,
    service: WebinarServiceDep,
) -> WebinarPlaybackSchema:
    embed_url = await service.generate_webinar_embed_url(webinar_slug, current_user.id)
    return WebinarPlaybackSchema(embed_url=embed_url)
