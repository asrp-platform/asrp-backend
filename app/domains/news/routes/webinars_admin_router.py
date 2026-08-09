from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi_exception_responses import Responses

from app.core.common.request_params import OrderingParamsDep, PaginationParamsDep
from app.core.common.responses import PaginatedResponse
from app.domains.news.filters import WebinarFilters
from app.domains.news.schemas import CreateWebinarSchema, UpdateWebinarSchema, WebinarBaseSchema
from app.domains.news.services import WebinarServiceDep
from app.domains.shared.deps import get_admin_user


router = APIRouter(
    prefix="/webinars",
    tags=["Admin: Webinars"],
    dependencies=[Depends(get_admin_user)],
)


class AdminWebinarResponses(Responses):
    NOT_AUTHORIZED = 401, "Not authorized"
    PERMISSION_ERROR = 403, "Not enough permissions"


@router.get("", responses=AdminWebinarResponses.responses)
async def get_webinars_paginated_counted(
    service: WebinarServiceDep,
    params: PaginationParamsDep,
    ordering: OrderingParamsDep = None,
    filters: Annotated[WebinarFilters, Depends()] = None,
) -> PaginatedResponse[WebinarBaseSchema]:
    data, count = await service.get_all_paginated_counted(
        order_by=ordering,
        filters=filters.model_dump(exclude_none=True),
        limit=params["limit"],
        offset=params["offset"],
        open_transaction=True,
    )
    return PaginatedResponse(
        count=count,
        data=data,
        page=params["page"],
        page_size=params["page_size"],
    )


@router.post("", responses=AdminWebinarResponses.responses)
async def create_webinar(
    service: WebinarServiceDep,
    body: CreateWebinarSchema,
) -> WebinarBaseSchema:
    return await service.create_webinar(
        open_transaction=True,
        **body.model_dump(),
    )


class UpdateWebinarResponses(AdminWebinarResponses):
    WEBINAR_NOT_FOUND = 404, "Webinar with provided ID not found"


@router.patch(
    "/{webinar_id}",
    responses=UpdateWebinarResponses.responses,
)
async def update_webinar(
    webinar_id: int,
    service: WebinarServiceDep,
    body: UpdateWebinarSchema,
) -> WebinarBaseSchema:
    return await service.update_webinar(
        webinar_id,
        open_transaction=True,
        **body.model_dump(exclude_unset=True),
    )


class DeleteWebinarResponses(AdminWebinarResponses):
    WEBINAR_NOT_FOUND = 404, "Webinar with provided ID not found"


@router.delete(
    "/{webinar_id}",
    responses=DeleteWebinarResponses.responses,
    summary="Delete webinar by ID",
)
async def delete_webinar(
    webinar_id: int,
    service: WebinarServiceDep,
) -> int:
    return await service.delete_webinar(webinar_id, open_transaction=True)
