from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Annotated, Any

from fastapi import Depends
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import selectinload

from app.core.common.exceptions import InvalidMimeTypeError, NotFoundError, PermissionDeniedError
from app.core.utils.save_file import save_file
from app.domains.memberships.models import UserMembership
from app.domains.news.filters import WebinarStartFilterEnum
from app.domains.news.models import News, Webinar, WebinarRegisteredUsers
from app.domains.news.schemas import UserWebinarSchema, WebinarBaseSchema
from app.domains.shared.transaction_managers import TransactionManagerDep
from app.domains.shared.types import FileData


def has_member_access(membership: UserMembership | None) -> bool:
    return bool(membership and membership.is_active and not membership.terminated and not membership.is_suspended)


def serialize_user_webinar(
    webinar: Webinar,
    *,
    user_id: int | None,
    membership: UserMembership | None,
) -> UserWebinarSchema:
    is_registered = user_id is not None and any(user.id == user_id for user in webinar.registered_users)
    response = UserWebinarSchema.model_validate({
        **WebinarBaseSchema.model_validate(webinar, from_attributes=True).model_dump(),
        "is_registered": is_registered,
    })
    can_view_links = user_id is not None and (not webinar.member_only or has_member_access(membership))
    now = datetime.now(timezone.utc)
    can_join = can_view_links and is_registered and webinar.starts_at <= now <= webinar.ends_at

    return response.model_copy(
        update={
            "registration_link": response.registration_link if can_view_links else None,
            "join_link": response.join_link if can_join else None,
            "recording_link": response.recording_link if can_view_links else None,
        },
    )


class NewsService:
    def __init__(self, transaction_manager: TransactionManagerDep):
        self.transaction_manager = transaction_manager

    async def get_all_paginated_counted(
        self, limit: int = None, offset: int = None, order_by: str = None, filters: dict[str, Any] = None
    ):
        async with self.transaction_manager:
            return await self.transaction_manager.news_repository.list(limit, offset, order_by, filters)

    async def create_news(self, **kwargs) -> News:
        async with self.transaction_manager:
            return await self.transaction_manager.news_repository.create(**kwargs)

    async def update_news(self, news_id: int, update_data: dict[str | Any]) -> None:
        async with self.transaction_manager:
            news = await self.transaction_manager.news_repository.get_first_by_kwargs(id=news_id)
            if news is None:
                raise NotFoundError("News with provided ID not found")
            await self.transaction_manager.news_repository.update(news_id, **update_data)

    async def get_news_by_id(self, news_id: int) -> News:
        async with self.transaction_manager:
            news = await self.transaction_manager.news_repository.get_first_by_kwargs(id=news_id)
            if news is None:
                raise NotFoundError("News with provided ID not found")
            return news

    async def set_news_deleted(self, news_id):
        async with self.transaction_manager:
            news = await self.transaction_manager.news_repository.get_first_by_kwargs(id=news_id)
            if news is None:
                raise NotFoundError("News with provided ID not found")
            await self.transaction_manager.news_repository.update(news_id, is_deleted=True)

    async def upload_image(self, file_data: FileData) -> Path:
        if not file_data.content_type.startswith("image/"):
            raise InvalidMimeTypeError("Invalid image content type")

        return await save_file(file_data, Path("path"))


class WebinarsService:
    def __init__(self, transaction_manager: TransactionManagerDep):
        self._tm = transaction_manager

    async def get_all_paginated_counted(
        self,
        limit: int = None,
        offset: int = None,
        order_by: str = None,
        filters: dict[str, Any] = None,
        *,
        open_transaction: bool = False,
    ) -> [list[Webinar], int]:
        filters = self._apply_start_filter(filters)

        if open_transaction:
            async with self._tm:
                return await self._tm.webinar_repository.list(limit, offset, order_by, filters)

        return await self._tm.webinar_repository.list(limit, offset, order_by, filters)

    async def get_user_webinars_paginated_counted(
        self,
        *,
        user_id: int | None,
        limit: int = None,
        offset: int = None,
        order_by: str = None,
        filters: dict[str, Any] = None,
    ) -> tuple[list[UserWebinarSchema], int]:
        async with self._tm:
            membership = None
            if user_id is not None:
                membership = await self._tm.user_membership_repository.get_first_by_kwargs(user_id=user_id)

            stmt = select(Webinar).options(selectinload(Webinar.registered_users))
            webinars, count = await self._tm.webinar_repository.list(
                limit,
                offset,
                order_by,
                self._apply_start_filter(filters),
                stmt=stmt if user_id is not None else None,
            )

            return [
                serialize_user_webinar(webinar, user_id=user_id, membership=membership) for webinar in webinars
            ], count

    @staticmethod
    def _apply_start_filter(filters: dict[str, Any]) -> dict[str, Any]:
        filters = (filters or {}).copy()
        webinar_start_status = filters.pop("status", WebinarStartFilterEnum.ALL)
        now = datetime.now(timezone.utc)

        if webinar_start_status == WebinarStartFilterEnum.UPCOMING:
            filters["ends_at__gte"] = now
        elif webinar_start_status == WebinarStartFilterEnum.PAST:
            filters["ends_at__lte"] = now
        return filters

    async def create_webinar(self, *, open_transaction=False, **kwargs) -> Webinar:
        if open_transaction:
            async with self._tm:
                return await self._tm.webinar_repository.create(**kwargs)

        return await self._tm.webinar_repository.create(**kwargs)

    async def delete_webinar(self, webinar_id: int, *, open_transaction: bool = False):
        if open_transaction:
            async with self._tm:
                return await self._tm.webinar_repository.mark_as_deleted(webinar_id)
        return await self._tm.webinar_repository.mark_as_deleted(webinar_id)

    async def update_webinar(
        self,
        webinar_id: int,
        *,
        open_transaction: bool = False,
        **kwargs,
    ) -> Webinar:
        if starts_at := kwargs.get("starts_at"):
            kwargs["ends_at"] = starts_at + timedelta(hours=2)

        if open_transaction:
            async with self._tm:
                return await self._tm.webinar_repository.update(webinar_id, **kwargs)
        return await self._tm.webinar_repository.update(webinar_id, **kwargs)

    async def register_for_webinar(self, webinar_slug: str, user_id: int) -> None:
        async with self._tm:
            stmt = select(Webinar).options(selectinload(Webinar.registered_users))
            webinar = await self._tm.webinar_repository.get_first_by_kwargs(slug=webinar_slug, stmt=stmt)
            if webinar is None:
                raise NotFoundError("Webinar with provided slug not found")
            user = await self._tm.user_repository.get_first_by_kwargs(id=user_id)
            if user is None:
                raise NotFoundError("User with provided ID not found")
            membership = await self._tm.user_membership_repository.get_first_by_kwargs(user_id=user_id)
            if webinar.member_only and not has_member_access(membership):
                raise PermissionDeniedError("Active membership is required to register for this webinar")

            statement = (
                insert(WebinarRegisteredUsers)
                .values(webinar_id=webinar.id, user_id=user.id)
                .on_conflict_do_nothing(
                    index_elements=["webinar_id", "user_id"],
                )
            )
            await self._tm.execute(statement)


NewsServiceDep = Annotated[NewsService, Depends()]
WebinarServiceDep = Annotated[WebinarsService, Depends()]
