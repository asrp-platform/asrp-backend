from datetime import datetime, timezone
from pathlib import Path
from typing import Annotated, Any

from fastapi import Depends
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import selectinload

from app.core.common.exceptions import InvalidMimeTypeError, NotFoundError
from app.core.utils.save_file import save_file
from app.domains.news.filters import WebinarStartFilterEnum
from app.domains.news.models import News, Webinar, WebinarRegisteredUsers
from app.domains.shared.transaction_managers import TransactionManagerDep
from app.domains.shared.types import FileData


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
        webinar_start_status = filters.pop("status")
        now = datetime.now(timezone.utc)

        if webinar_start_status == WebinarStartFilterEnum.UPCOMING:
            filters["starts_at__gte"] = now
        elif webinar_start_status == WebinarStartFilterEnum.PAST:
            filters["starts_at__lte"] = now

        if open_transaction:
            async with self._tm:
                return await self._tm.webinar_repository.list(limit, offset, order_by, filters)

        return await self._tm.webinar_repository.list(limit, offset, order_by, filters)

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

    async def register_for_webinar(self, webinar_slug: str, user_id: int) -> None:
        async with self._tm:
            stmt = select(Webinar).options(selectinload(Webinar.registered_users))
            webinar = await self._tm.webinar_repository.get_first_by_kwargs(slug=webinar_slug, stmt=stmt)
            if webinar is None:
                raise NotFoundError("Webinar with provided slug not found")
            user = await self._tm.user_repository.get_first_by_kwargs(id=user_id)
            if user is None:
                raise NotFoundError("User with provided ID not found")

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
