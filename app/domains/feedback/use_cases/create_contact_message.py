from typing import Annotated

from fastapi import Depends

from app.domains.feedback.schemas import ContactMessageResponseSchema, CreateContactMessageSchema
from app.domains.feedback.services import ContactMessageServiceDep


class CreateContactMessageUseCase:
    def __init__(self, feedback_service: ContactMessageServiceDep):
        self.__feedback_service = feedback_service

    async def execute(self, data: CreateContactMessageSchema) -> ContactMessageResponseSchema:
        async with self.__feedback_service.transaction_manager:
            return await self.__feedback_service.create(data.model_dump(mode="json"))


CreateContactMessageUseCaseDep = Annotated[
    CreateContactMessageUseCase,
    Depends(CreateContactMessageUseCase),
]
