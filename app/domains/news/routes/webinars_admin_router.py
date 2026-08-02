from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi_exception_responses import Responses

from app.core.common.request_params import OrderingParamsDep, PaginationParamsDep
from app.core.common.responses import PaginatedResponse
from app.domains.news.filters import WebinarFilters
from app.domains.news.schemas import CreateWebinarSchema, WebinarBaseSchema
from app.domains.news.services import WebinarServiceDep


router = APIRouter(prefix="/webinars", tags=["Admin: Webinars"])


@router.get("")
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


@router.post("")
async def create_webinar(
    service: WebinarServiceDep,
    body: CreateWebinarSchema,
) -> WebinarBaseSchema:
    return await service.create_webinar(
        open_transaction=True,
        **body.model_dump(),
    )


class DeleteWebinarResponses(Responses):
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
