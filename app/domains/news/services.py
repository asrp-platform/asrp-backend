import hashlib
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Annotated, Any

from fastapi import Depends
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import selectinload

from app.core.common.exceptions import InvalidMimeTypeError, NotFoundError, PermissionDeniedError
from app.core.config import settings
from app.core.storage.storage_factory import FileStorageDep
from app.core.utils.save_file import generate_filename
from app.domains.memberships.models import UserMembership
from app.domains.memberships.utils import has_member_access
from app.domains.news.filters import WebinarStartFilterEnum
from app.domains.news.models import News, Webinar, WebinarRegisteredUsers
from app.domains.shared.transaction_managers import TransactionManagerDep
from app.domains.shared.types import FileData
from app.domains.users.models import User


class NewsService:
    def __init__(
        self,
        transaction_manager: TransactionManagerDep,
        file_storage: FileStorageDep,
    ):
        self._tm = transaction_manager
        self._file_storage = file_storage

    async def get_news_paginated_counted(
        self,
        limit: int = None,
        offset: int = None,
        order_by: str = None,
        filters: dict[str, Any] = None,
        *,
        open_transaction: bool = False,
    ):
        if open_transaction:
            async with self._tm:
                return await self._tm.news_repository.list(limit, offset, order_by, filters)
        return await self._tm.news_repository.list(limit, offset, order_by, filters)

    async def create_news(self, **kwargs) -> News:
        async with self._tm:
            return await self._tm.news_repository.create(**kwargs)

    async def update_news(self, news_id: int, update_data: dict[str, Any]) -> News:
        async with self._tm:
            return await self._tm.news_repository.update(news_id, **update_data)

    async def get_news_by_id(self, news_id: int) -> News:
        async with self._tm:
            news = await self._tm.news_repository.get_first_by_kwargs(id=news_id)
            if news is None:
                raise NotFoundError("News with provided ID not found")
            return news

    async def delete_news_by_id(self, news_id: int) -> int:
        async with self._tm:
            return await self._tm.news_repository.mark_as_deleted(row_id=news_id)

    async def upload_image(self, file_data: FileData) -> Path:
        if not file_data.content_type.startswith("image/"):
            raise InvalidMimeTypeError("Invalid image content type")

        filename = generate_filename(file_data.filename, prefix="news")
        file_data = await self._file_storage.upload_file(object_key=filename, file_content=file_data.content)
        return await self._file_storage.get_file_url(file_data.object_key)


class WebinarsService:
    BUNNY_EMBED_LIFESPAN = 60 * 60

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
    ) -> tuple[list[Webinar], int]:
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
    ) -> tuple[list[Webinar], int, UserMembership | None]:
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

            return webinars, count, membership

    async def generate_webinar_embed_url(self, webinar_slug: str, user_id: int) -> str | None:
        async with self._tm:
            webinar = await self._tm.webinar_repository.get_first_by_kwargs(slug=webinar_slug)
            if webinar is None:
                raise NotFoundError("Webinar with provided slug not found")

            if webinar.member_only:
                membership = await self._tm.user_membership_repository.get_first_by_kwargs(user_id=user_id)
                if not has_member_access(membership):
                    raise PermissionDeniedError("Active membership is required to view this webinar")

            if webinar.bunny_video_id is None:
                return None

            return self.generate_bunny_embed_url(
                library_id=settings.BUNNY_LIBRARY_ID,
                video_id=webinar.bunny_video_id,
                token_key=settings.BUNNY_STREAM_TOKEN_KEY,
                expires_in=self.BUNNY_EMBED_LIFESPAN,
            )

    @staticmethod
    def generate_bunny_embed_url(
        library_id: int,
        video_id: str,
        token_key: str,
        expires_in: int = 1800,
    ) -> str:
        expires = int(time.time()) + expires_in

        raw_token = f"{token_key}{video_id}{expires}"

        token = hashlib.sha256(raw_token.encode("utf-8")).hexdigest()

        return f"https://iframe.mediadelivery.net/embed/{library_id}/{video_id}?token={token}&expires={expires}"

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
            webinar = await self._tm.webinar_repository.get_first_by_kwargs(slug=webinar_slug)
            if webinar is None:
                raise NotFoundError("Webinar with provided slug not found")
            user = await self._tm.user_repository.get_first_by_kwargs(id=user_id)
            if user is None:
                raise NotFoundError("User with provided ID not found")
            if webinar.member_only:
                membership = await self._tm.user_membership_repository.get_first_by_kwargs(user_id=user_id)
                if not has_member_access(membership):
                    raise PermissionDeniedError("Active membership is required to register for this webinar")

            statement = (
                insert(WebinarRegisteredUsers)
                .values(webinar_id=webinar.id, user_id=user.id)
                .on_conflict_do_nothing(
                    index_elements=["webinar_id", "user_id"],
                )
            )
            await self._tm.execute(statement)

    async def get_registered_users_paginated_counted(
        self,
        webinar_id: int,
        *,
        limit: int | None = None,
        offset: int | None = None,
        order_by: str | None = None,
    ) -> tuple[list[User], int]:
        async with self._tm:
            webinar = await self._tm.webinar_repository.get_first_by_kwargs(id=webinar_id)
            if webinar is None:
                raise NotFoundError("Webinar with provided ID not found")

            return await self._tm.webinar_repository.list_registered_users(
                webinar_id,
                limit=limit,
                offset=offset,
                order_by=order_by,
            )


NewsServiceDep = Annotated[NewsService, Depends()]
WebinarServiceDep = Annotated[WebinarsService, Depends()]
