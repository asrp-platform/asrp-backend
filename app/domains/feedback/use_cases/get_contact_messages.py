from typing import Annotated

from fastapi import Depends

from app.core.utils.permissions import check_permissions
from app.domains.feedback.services import ContactMessageServiceDep


class GetContactMessagesUseCase:
    def __init__(self, feedback_service: ContactMessageServiceDep):
        self.__feedback_service = feedback_service

    async def execute(
        self,
        permissions: list[str],
        *,
        limit: int | None = None,
        offset: int | None = None,
        order_by: str | None = None,
        filters: dict | None = None,
    ):
        check_permissions("feedback.view", permissions)
        async with self.__feedback_service.transaction_manager:
            return await self.__feedback_service.list(
                limit=limit,
                offset=offset,
                order_by=order_by,
                filters=filters,
            )


GetContactMessagesUseCaseDep = Annotated[
    GetContactMessagesUseCase,
    Depends(GetContactMessagesUseCase),
]
