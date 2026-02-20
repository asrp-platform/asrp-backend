from typing import Annotated, Any

from fastapi import Depends

from app.domains.emails.plugins.gmail_plugin import GmailPlugin
from app.domains.emails.services import get_email_service
from app.domains.feedback.infrastructure import FeedbackUnitOfWork, get_feedback_unit_of_work
from app.domains.feedback.schemas import CreateContactMessageSchema


class FeedbackService:
    def __init__(self, uow):
        self.uow: FeedbackUnitOfWork = uow
        self.email_provider = get_email_service(GmailPlugin)

    async def create_contact_message(self, data: CreateContactMessageSchema):
        message_data = data.model_dump()
        async with self.uow:
            return await self.uow.contact_message_repository.create(**message_data)

    async def get_all_paginated_counted(
        self, limit: int = None, offset: int = None, order_by: str = None, filters: dict[str, Any] = None
    ):
        async with self.uow:
            return await self.uow.contact_message_repository.list(limit, offset, order_by, filters)

    async def answer_contact_message(self, contact_message_id: int, subject, answer_message: str, plain: bool = True):
        async with self.uow:
            contact_message = await self.uow.contact_message_repository.get_first_by_kwargs(id=contact_message_id)

            if contact_message is None:
                raise ValueError("There is no contact message with provided id")

            message_reply = await self.uow.contact_message_reply_repository.create(
                contact_message_id=contact_message.id, answer=answer_message
            )

            await self.uow.contact_message_repository.update(contact_message_id, {"answered": True})

        await self.email_provider.send_email(
            to=contact_message.email,
            subject=subject,
            body=answer_message,
        )

        return message_reply


def get_feedback_service(
    uow: Annotated[FeedbackUnitOfWork, Depends(get_feedback_unit_of_work)],
) -> FeedbackService:
    return FeedbackService(uow)


FeedbackServiceDep = Annotated[FeedbackService, Depends(get_feedback_service)]
