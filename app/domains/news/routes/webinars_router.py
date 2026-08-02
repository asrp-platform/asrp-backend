from typing import Annotated

from fastapi import APIRouter, Depends

from app.core.common.request_params import OrderingParamsDep, PaginationParamsDep
from app.core.common.responses import NotAuthorizedResponses, PaginatedResponse
from app.domains.memberships.models import UserMembership
from app.domains.memberships.services import UserMembershipServiceDep
from app.domains.news.filters import WebinarFilters
from app.domains.news.models import Webinar
from app.domains.news.schemas import WebinarBaseSchema
from app.domains.news.services import WebinarServiceDep
from app.domains.shared.deps import CurrentUserDep, OptionalCurrentUserDep


router = APIRouter(prefix="/webinars", tags=["Webinars"])


def has_member_access(membership: UserMembership | None) -> bool:
    return bool(membership and membership.is_active and not membership.terminated and not membership.is_suspended)


def serialize_webinar(
    webinar: Webinar,
    *,
    is_authenticated: bool,
    has_active_membership: bool,
) -> WebinarBaseSchema:
    response = WebinarBaseSchema.model_validate(webinar, from_attributes=True)
    can_view_links = is_authenticated and (not webinar.member_only or has_active_membership)
    if can_view_links:
        return response

    return response.model_copy(
        update={
            "registration_link": None,
            "join_link": None,
            "recording_link": None,
        }
    )


@router.get("", response_model_exclude_none=True)
async def get_webinars_paginated_counted(
    service: WebinarServiceDep,
    membership_service: UserMembershipServiceDep,
    current_user: OptionalCurrentUserDep,
    params: PaginationParamsDep,
    ordering: OrderingParamsDep = None,
    filters: Annotated[WebinarFilters, Depends()] = None,
) -> PaginatedResponse[WebinarBaseSchema]:
    membership = None
    if current_user is not None:
        membership = await membership_service.get_user_membership_by_user_id(current_user.id)
    has_active_membership = has_member_access(membership)

    webinars, count = await service.get_all_paginated_counted(
        order_by=ordering,
        filters=filters.model_dump(exclude_none=True),
        limit=params["limit"],
        offset=params["offset"],
        open_transaction=True,
    )

    data = [
        serialize_webinar(
            webinar,
            is_authenticated=current_user is not None,
            has_active_membership=has_active_membership,
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
