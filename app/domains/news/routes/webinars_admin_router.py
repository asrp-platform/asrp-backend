from typing import Annotated

from fastapi import APIRouter, Depends

from app.core.common.request_params import OrderingParamsDep, PaginationParamsDep
from app.core.common.responses import PaginatedResponse
from app.domains.news.filters import WebinarFilters
from app.domains.news.schemas import WebinarBaseSchema
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
    )
    return PaginatedResponse(
        count=count,
        data=data,
        page=params["page"],
        page_size=params["page_size"],
    )
