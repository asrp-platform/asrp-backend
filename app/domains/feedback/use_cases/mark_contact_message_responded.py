from typing import Annotated

from fastapi import Depends

from app.core.utils.permissions import check_permissions
from app.domains.feedback.services import ContactMessageServiceDep


class MarkContactMessageRespondedUseCase:
    def __init__(self, feedback_service: ContactMessageServiceDep):
        self.__feedback_service = feedback_service

    async def execute(self, message_id: int, permissions: list[str]) -> None:
        check_permissions("feedback.update", permissions)
        async with self.__feedback_service.transaction_manager:
            await self.__feedback_service.mark_responded_manually(message_id)


MarkContactMessageRespondedUseCaseDep = Annotated[
    MarkContactMessageRespondedUseCase,
    Depends(MarkContactMessageRespondedUseCase),
]
