from datetime import date, datetime, time, timedelta, timezone
from typing import Annotated, Any, Sequence

from fastapi import Depends
from sqlalchemy import func, select

from app.core.common.exceptions import NotFoundError, ResourceAlreadyExistsError
from app.domains.emails.email_queue import EmailQueueDep
from app.domains.feedback.models import FeedbackAdditionalInfo
from app.domains.shared.transaction_managers import TransactionManager, TransactionManagerDep


class ContactMessageService:
    """Persistence and notification operations for contact messages.

    Transaction boundaries belong to the calling use case.
    """

    def __init__(self, transaction_manager: TransactionManager, email_queue: EmailQueueDep):
        self.transaction_manager = transaction_manager
        self.email_queue = email_queue

    async def create(self, data: dict):
        return await self.transaction_manager.contact_message_repository.create(**data)

    async def list(
        self, limit: int | None = None, offset: int | None = None, order_by: str | None = None, filters=None
    ):
        return await self.transaction_manager.contact_message_repository.list(limit, offset, order_by, filters)

    async def create_answer(self, contact_message_id: int, answer_message: str):
        contact_message = await self.transaction_manager.contact_message_repository.get_first_by_kwargs(
            id=contact_message_id
        )
        if contact_message is None:
            raise NotFoundError("There is no contact message with provided id")

        reply = await self.transaction_manager.contact_message_reply_repository.create(
            contact_message_id=contact_message.id,
            answer=answer_message,
        )
        await self.transaction_manager.contact_message_repository.update(contact_message_id, answered=True)
        return reply, contact_message.email

    async def send_answer(self, recipient: str, subject: str, answer_message: str) -> None:
        await self.email_queue.send_email(to=recipient, subject=subject, body=answer_message)


class FeedbackAdditionalInfoService:
    """Persistence and reporting operations for additional feedback data.

    Methods do not open or commit transactions. This is required because create()
    is also used inside the membership-registration transaction.
    """

    def __init__(self, transaction_manager: TransactionManager):
        self.transaction_manager = transaction_manager

    async def create(self, user_id: int, **kwargs) -> FeedbackAdditionalInfo:
        existing = await self.transaction_manager.feedback_additional_info_repository.get_first_by_kwargs(
            user_id=user_id
        )
        if existing is not None:
            raise ResourceAlreadyExistsError("Additional detail for User with provided ID is already exists")
        return await self.transaction_manager.feedback_additional_info_repository.create(user_id=user_id, **kwargs)

    async def get_hear_about_stats(
        self,
        date_from: date | None = None,
        date_to: date | None = None,
    ) -> list[dict[str, Any]]:
        stmt = select(FeedbackAdditionalInfo.hear_about_asrp, func.count().label("count")).where(
            FeedbackAdditionalInfo._deleted.is_(False)
        )
        stmt = self.__apply_date_range(stmt, date_from, date_to)
        stmt = stmt.group_by(FeedbackAdditionalInfo.hear_about_asrp)
        result = await self.transaction_manager._session.execute(stmt)
        return [{"option": row[0], "count": row[1]} for row in result.all()]

    async def get_interests_paginated_counted(
        self,
        limit: int | None = None,
        offset: int | None = None,
        search: str | None = None,
        has_telegram: bool | None = None,
        date_from: date | None = None,
        date_to: date | None = None,
    ) -> tuple[Sequence[FeedbackAdditionalInfo], int]:
        stmt = (
            select(FeedbackAdditionalInfo)
            .where(FeedbackAdditionalInfo.interest_description.isnot(None), FeedbackAdditionalInfo._deleted.is_(False))
            .order_by(FeedbackAdditionalInfo.created_at.desc())
        )
        count_stmt = (
            select(func.count())
            .select_from(FeedbackAdditionalInfo)
            .where(FeedbackAdditionalInfo.interest_description.isnot(None), FeedbackAdditionalInfo._deleted.is_(False))
        )

        if search:
            condition = FeedbackAdditionalInfo.interest_description.ilike(f"%{search}%")
            stmt = stmt.where(condition)
            count_stmt = count_stmt.where(condition)

        if has_telegram is not None:
            condition = (
                (FeedbackAdditionalInfo.tg_username.isnot(None), FeedbackAdditionalInfo.tg_username != "")
                if has_telegram
                else ((FeedbackAdditionalInfo.tg_username.is_(None)) | (FeedbackAdditionalInfo.tg_username == ""))
            )
            if isinstance(condition, tuple):
                stmt = stmt.where(*condition)
                count_stmt = count_stmt.where(*condition)
            else:
                stmt = stmt.where(condition)
                count_stmt = count_stmt.where(condition)

        stmt = self.__apply_date_range(stmt, date_from, date_to)
        count_stmt = self.__apply_date_range(count_stmt, date_from, date_to)

        if limit is not None and offset is not None:
            stmt = stmt.offset(offset).limit(limit)

        data = (await self.transaction_manager._session.execute(stmt)).scalars().all()
        count = (await self.transaction_manager._session.execute(count_stmt)).scalar_one()
        return data, count

    @staticmethod
    def __apply_date_range(stmt, date_from: date | None, date_to: date | None):
        if date_from is not None:
            from_dt = datetime.combine(date_from, time.min).replace(tzinfo=timezone.utc)
            stmt = stmt.where(FeedbackAdditionalInfo.created_at >= from_dt)
        if date_to is not None:
            to_dt_exclusive = datetime.combine(date_to + timedelta(days=1), time.min).replace(tzinfo=timezone.utc)
            stmt = stmt.where(FeedbackAdditionalInfo.created_at < to_dt_exclusive)
        return stmt


def get_contact_message_service(
    transaction_manager: TransactionManagerDep,
    email_queue: EmailQueueDep,
) -> ContactMessageService:
    return ContactMessageService(transaction_manager, email_queue)


def get_feedback_additional_info_service(
    transaction_manager: TransactionManagerDep,
) -> FeedbackAdditionalInfoService:
    return FeedbackAdditionalInfoService(transaction_manager)


ContactMessageServiceDep = Annotated[ContactMessageService, Depends(get_contact_message_service)]
FeedbackAdditionalInfoServiceDep = Annotated[
    FeedbackAdditionalInfoService,
    Depends(get_feedback_additional_info_service),
]
