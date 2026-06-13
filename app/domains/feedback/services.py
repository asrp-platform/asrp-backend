from datetime import date, datetime, time, timedelta, timezone
from typing import Annotated, Any, Sequence

from fastapi import Depends
from sqlalchemy import func, select

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

    async def get_hear_about_stats(
        self,
        date_from: date | None = None,
        date_to: date | None = None,
    ) -> list[dict[str, Any]]:
        stmt = select(FeedbackAdditionalInfo.hear_about_asrp, func.count().label("count")).where(
            FeedbackAdditionalInfo._deleted.is_(False)
        )

        if date_from is not None:
            from_dt = datetime.combine(date_from, time.min).replace(tzinfo=timezone.utc)
            stmt = stmt.where(FeedbackAdditionalInfo.created_at >= from_dt)

        if date_to is not None:
            to_dt_exclusive = datetime.combine(date_to + timedelta(days=1), time.min).replace(tzinfo=timezone.utc)
            stmt = stmt.where(FeedbackAdditionalInfo.created_at < to_dt_exclusive)

        stmt = stmt.group_by(FeedbackAdditionalInfo.hear_about_asrp)

        async with self.transaction_manager:
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
            stmt = stmt.where(FeedbackAdditionalInfo.interest_description.ilike(f"%{search}%"))
            count_stmt = count_stmt.where(FeedbackAdditionalInfo.interest_description.ilike(f"%{search}%"))

        if has_telegram is not None:
            if has_telegram:
                stmt = stmt.where(
                    FeedbackAdditionalInfo.tg_username.isnot(None), FeedbackAdditionalInfo.tg_username != ""
                )
                count_stmt = count_stmt.where(
                    FeedbackAdditionalInfo.tg_username.isnot(None), FeedbackAdditionalInfo.tg_username != ""
                )
            else:
                stmt = stmt.where(
                    (FeedbackAdditionalInfo.tg_username.is_(None)) | (FeedbackAdditionalInfo.tg_username == "")
                )
                count_stmt = count_stmt.where(
                    (FeedbackAdditionalInfo.tg_username.is_(None)) | (FeedbackAdditionalInfo.tg_username == "")
                )

        if date_from is not None:
            from_dt = datetime.combine(date_from, time.min).replace(tzinfo=timezone.utc)
            stmt = stmt.where(FeedbackAdditionalInfo.created_at >= from_dt)
            count_stmt = count_stmt.where(FeedbackAdditionalInfo.created_at >= from_dt)

        if date_to is not None:
            to_dt_exclusive = datetime.combine(date_to + timedelta(days=1), time.min).replace(tzinfo=timezone.utc)
            stmt = stmt.where(FeedbackAdditionalInfo.created_at < to_dt_exclusive)
            count_stmt = count_stmt.where(FeedbackAdditionalInfo.created_at < to_dt_exclusive)

        if limit is not None and offset is not None:
            stmt = stmt.offset(offset).limit(limit)

        async with self.transaction_manager:
            data = (await self.transaction_manager._session.execute(stmt)).scalars().all()
            count = (await self.transaction_manager._session.execute(count_stmt)).scalar_one()
            return data, count


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
