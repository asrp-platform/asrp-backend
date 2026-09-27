from typing import Annotated

from fastapi import Depends

from app.core.utils.permissions import check_permissions
from app.domains.feedback.services import ContactMessageServiceDep


class AnswerContactMessageUseCase:
    def __init__(self, feedback_service: ContactMessageServiceDep):
        self.__feedback_service = feedback_service

    async def execute(
        self,
        message_id: int,
        subject: str,
        answer_message: str,
        permissions: list[str],
    ):
        check_permissions("feedback.update", permissions)
        async with self.__feedback_service.transaction_manager:
            reply, recipient = await self.__feedback_service.create_answer(message_id, answer_message)
        await self.__feedback_service.send_answer(recipient, subject, answer_message)
        return reply


AnswerContactMessageUseCaseDep = Annotated[
    AnswerContactMessageUseCase,
    Depends(AnswerContactMessageUseCase),
]
