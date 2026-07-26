from typing import Annotated

from fastapi import APIRouter, Depends

from app.core.common.request_params import OrderingParamsDep, PaginationParamsDep
from app.core.common.responses import InvalidRequestParamsResponses, PaginatedResponse, PermissionsResponses
from app.core.utils.permissions import check_permissions
from app.domains.payments.filters import PaymentsFilter
from app.domains.payments.schemas import PaymentReadSchema
from app.domains.payments.services import PaymentServiceDep
from app.domains.shared.deps import AdminPermissionsDep, get_admin_user


router = APIRouter(tags=["Admin: Payments"], prefix="/payments", dependencies=[Depends(get_admin_user)])


class PaymentListResponses(InvalidRequestParamsResponses, PermissionsResponses):
    pass


@router.get(
    "",
    summary="Get a list of payments",
    responses=PaymentListResponses.responses,
)
async def get_payments(
    permissions: AdminPermissionsDep,
    service: PaymentServiceDep,
    params: PaginationParamsDep,
    ordering: OrderingParamsDep = "-created_at",
    filters: Annotated[PaymentsFilter, Depends()] = None,
) -> PaginatedResponse[PaymentReadSchema]:
    check_permissions("payments.view", permissions)
    payments, count = await service.get_payments_paginated_counted(
        order_by=ordering,
        filters=filters.model_dump(exclude_none=True),
        limit=params["limit"],
        offset=params["offset"],
        open_transaction=True,
    )
    return PaginatedResponse(
        count=count,
        data=payments,
        page=params["page"],
        page_size=params["page_size"],
    )
