from typing import Annotated, Any

from fastapi import Depends

from app.domains.emails.plugins.gmail_plugin import GmailPlugin
from app.domains.emails.services import get_email_service
from app.domains.feedback.exceptions import FeedbackAdditionalInfoAlreadyExistsError
from app.domains.feedback.models import FeedbackAdditionalInfo
from app.domains.shared.transaction_managers import TransactionManager, TransactionManagerDep


class FeedbackService:
    def __init__(self, transaction_manager: TransactionManager):
        self.transaction_manager = transaction_manager
        self.email_provider = get_email_service(GmailPlugin)

    async def create_contact_message(self, data: dict):
        async with self.transaction_manager:
            return await self.transaction_manager.contact_message_repository.create(**data)

    async def get_all_paginated_counted(
        self, limit: int = None, offset: int = None, order_by: str = None, filters: dict[str, Any] = None
    ):
        async with self.transaction_manager:
            return await self.transaction_manager.contact_message_repository.list(limit, offset, order_by, filters)

    async def answer_contact_message(self, contact_message_id: int, subject, answer_message: str, plain: bool = True):
        async with self.transaction_manager:
            contact_message = await self.transaction_manager.contact_message_repository.get_first_by_kwargs(
                id=contact_message_id
            )

            if contact_message is None:
                raise ValueError("There is no contact message with provided id")

            message_reply = await self.transaction_manager.contact_message_reply_repository.create(
                contact_message_id=contact_message.id, answer=answer_message
            )

            await self.transaction_manager.contact_message_repository.update(contact_message_id, answered=True)

        await self.email_provider.send_email(
            to=contact_message.email,
            subject=subject,
            body=answer_message,
        )

        return message_reply


class FeedbackAdditionalInfoService:
    def __init__(self, transaction_manager: TransactionManager):
        self.transaction_manager = transaction_manager

    async def create_feedback_additional_info(self, user_id: int, **kwargs) -> FeedbackAdditionalInfo:
        feedback_additional_info = (
            await self.transaction_manager.feedback_additional_info_repository.get_first_by_kwargs(user_id=user_id)
        )
        if feedback_additional_info is not None:
            raise FeedbackAdditionalInfoAlreadyExistsError(
                "Additional detail for User with provided ID is already exists"
            )

        return await self.transaction_manager.feedback_additional_info_repository.create(user_id=user_id, **kwargs)


def get_feedback_additional_info_service(
    transaction_manager: TransactionManagerDep,
) -> FeedbackAdditionalInfoService:
    return FeedbackAdditionalInfoService(transaction_manager)


def get_feedback_service(
    transaction_manager: TransactionManagerDep,
) -> FeedbackService:
    return FeedbackService(transaction_manager)


FeedbackServiceDep = Annotated[FeedbackService, Depends(get_feedback_service)]
FeedbackAdditionalInfoServiceDep = Annotated[
    FeedbackAdditionalInfoService, Depends(get_feedback_additional_info_service)
]
