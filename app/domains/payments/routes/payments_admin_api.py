from typing import Annotated

from fastapi import APIRouter, Depends

from app.core.common.request_params import OrderingParamsDep, PaginationParamsDep
from app.core.common.responses import InvalidRequestParamsResponses, PaginatedResponse
from app.core.database.base_repository import InvalidOrderAttributeError
from app.domains.payments.filters import PaymentsFilter
from app.domains.payments.schemas import PaymentReadSchema
from app.domains.payments.services import PaymentServiceDep
from app.domains.shared.deps import get_admin_user

router = APIRouter(tags=["Admin: Payments"], prefix="/payments", dependencies=[Depends(get_admin_user)])


class PaymentListResponses(InvalidRequestParamsResponses):
    pass


@router.get("", responses=PaymentListResponses.responses)
async def get_payments(
    service: PaymentServiceDep,
    params: PaginationParamsDep,
    ordering: OrderingParamsDep = "-created_at",
    filters: Annotated[PaymentsFilter, Depends()] = None,
) -> PaginatedResponse[PaymentReadSchema]:
    try:
        payments, count = await service.get_payments_paginated_counted(
            order_by=ordering,
            filters=filters.model_dump(exclude_none=True),
            limit=params["limit"],
            offset=params["offset"],
        )
        return PaginatedResponse(
            count=count,
            data=payments,
            page=params["page"],
            page_size=params["page_size"],
        )
    except InvalidOrderAttributeError:
        raise PaymentListResponses.INVALID_SORTER_FIELD
