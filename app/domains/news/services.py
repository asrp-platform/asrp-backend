import hashlib
import logging
import time
from copy import deepcopy
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Annotated, Any

from fastapi import Depends
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import selectinload

from app.core.common.exceptions import InvalidMimeTypeError, NotFoundError, PayloadTooLargeError, PermissionDeniedError
from app.core.config import settings
from app.core.storage.storage_factory import FileStorageDep
from app.core.utils.save_file import generate_filename
from app.domains.memberships.models import UserMembership
from app.domains.memberships.utils import has_member_access
from app.domains.news.filters import WebinarStartFilterEnum
from app.domains.news.models import News, Webinar, WebinarRegisteredUsers
from app.domains.shared.transaction_managers import TransactionManagerDep
from app.domains.shared.types import FileData, StoredFile
from app.domains.users.models import User


logger = logging.getLogger(__name__)


@dataclass
class NewsDTO:
    id: int
    created_at: datetime
    updated_at: datetime
    title: str
    slug: str
    cover_key: str | None
    cover_url: str | None
    body: dict
    when: str | None
    where: str | None
    is_published: bool
    author_id: int


class NewsService:
    MAX_IMAGE_SIZE = 5 * 1024 * 1024
    ALLOWED_IMAGE_CONTENT_TYPES = {"image/jpeg", "image/png", "image/webp", "image/gif"}

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
    ) -> tuple[list[NewsDTO], int]:
        if open_transaction:
            async with self._tm:
                news, count = await self._tm.news_repository.list(limit, offset, order_by, filters)
                return await self._to_dtos(news), count

        news, count = await self._tm.news_repository.list(limit, offset, order_by, filters)
        return await self._to_dtos(news), count

    async def create_news(self, **kwargs) -> NewsDTO:
        if body := kwargs.get("body"):
            kwargs["body"] = self._normalize_body_image_keys(body)
        async with self._tm:
            news = await self._tm.news_repository.create(**kwargs)
            await self._tm.flush()
            return await self._to_dto(news)

    async def update_news(self, news_id: int, update_data: dict[str, Any]) -> NewsDTO:
        if body := update_data.get("body"):
            update_data["body"] = self._normalize_body_image_keys(body)

        async with self._tm:
            existing_news = await self._tm.news_repository.get_first_by_kwargs(id=news_id)
            if existing_news is None:
                raise NotFoundError("News with provided ID not found")

            old_image_keys = self._get_news_image_keys(existing_news)
            news = await self._tm.news_repository.update(news_id, **update_data)
            await self._tm.flush()
            new_image_keys = self._get_news_image_keys(news)
            dto = await self._to_dto(news)

        await self._delete_image_keys(old_image_keys - new_image_keys)
        return dto

    async def get_news_by_id(self, news_id: int) -> NewsDTO:
        async with self._tm:
            news = await self._tm.news_repository.get_first_by_kwargs(id=news_id)
            if news is None:
                raise NotFoundError("News with provided ID not found")
            return await self._to_dto(news)

    async def get_published_news_by_slug(self, slug: str) -> NewsDTO:
        async with self._tm:
            news = await self._tm.news_repository.get_first_by_kwargs(
                slug=slug,
                is_published=True,
            )
            if news is None:
                raise NotFoundError("News with provided slug not found")
            return await self._to_dto(news)

    async def delete_news_by_id(self, news_id: int) -> int:
        async with self._tm:
            news = await self._tm.news_repository.get_first_by_kwargs(id=news_id)
            if news is None:
                raise NotFoundError("News with provided ID not found")
            image_keys = self._get_news_image_keys(news)
            deleted_id = await self._tm.news_repository.mark_as_deleted(row_id=news_id)

        await self._delete_image_keys(image_keys)
        return deleted_id

    async def upload_image(self, file_data: FileData) -> StoredFile:
        if file_data.content_type not in self.ALLOWED_IMAGE_CONTENT_TYPES:
            raise InvalidMimeTypeError("Invalid image content type")
        if len(file_data.content) > self.MAX_IMAGE_SIZE:
            raise PayloadTooLargeError("Image must be smaller than 5 MB")

        filename = generate_filename(file_data.filename, prefix="news")
        file_data = await self._file_storage.upload_file(object_key=filename, file_content=file_data.content)
        file_url = await self._file_storage.get_file_url(file_data.object_key)

        return StoredFile(file_url=file_url, object_key=file_data.object_key)

    def _get_news_image_keys(self, news: News) -> set[str]:
        keys = self._extract_body_image_keys(news.body)
        if news.cover_key and news.cover_key.startswith("news/"):
            keys.add(news.cover_key)
        return keys

    def _extract_body_image_keys(self, body: dict) -> set[str]:
        keys: set[str] = set()

        def collect(node: Any) -> None:
            if isinstance(node, dict):
                if node.get("type") == "image":
                    attrs = node.get("attrs") or {}
                    object_key = attrs.get("objectKey") or self._file_storage.extract_object_key(
                        attrs.get("src"),
                        allowed_prefixes=["news/"],
                    )
                    if isinstance(object_key, str) and object_key.startswith("news/"):
                        keys.add(object_key)
                for value in node.values():
                    collect(value)
            elif isinstance(node, list):
                for item in node:
                    collect(item)

        collect(body)
        return keys

    async def _delete_image_keys(self, object_keys: set[str]) -> None:
        for object_key in object_keys:
            try:
                await self._file_storage.delete_file(object_key)
            except Exception:
                logger.exception("Failed to remove orphaned news image %s", object_key)

    async def _to_dtos(self, news: list[News]) -> list[NewsDTO]:
        return [await self._to_dto(item) for item in news]

    async def _to_dto(self, news: News) -> NewsDTO:
        cover_url = None
        if news.cover_key:
            cover_url = await self._file_storage.get_file_url(news.cover_key)

        return NewsDTO(
            id=news.id,
            created_at=news.created_at,
            updated_at=news.updated_at,
            title=news.title,
            slug=news.slug,
            cover_key=news.cover_key,
            cover_url=cover_url,
            body=await self._hydrate_body_image_urls(news.body),
            when=news.when,
            where=news.where,
            is_published=news.is_published,
            author_id=news.author_id,
        )

    def _normalize_body_image_keys(self, body: dict) -> dict:
        normalized_body = deepcopy(body)

        def normalize_node(node: Any) -> None:
            if isinstance(node, dict):
                if node.get("type") == "image":
                    attrs = node.setdefault("attrs", {})
                    object_key = attrs.get("objectKey") or self._file_storage.extract_object_key(
                        attrs.get("src"),
                        allowed_prefixes=["news/"],
                    )
                    if object_key:
                        attrs["src"] = object_key
                        attrs["objectKey"] = object_key

                for value in node.values():
                    normalize_node(value)
            elif isinstance(node, list):
                for item in node:
                    normalize_node(item)

        normalize_node(normalized_body)
        return normalized_body

    async def _hydrate_body_image_urls(self, body: dict) -> dict:
        hydrated_body = deepcopy(body)

        async def hydrate_node(node: Any) -> None:
            if isinstance(node, dict):
                if node.get("type") == "image":
                    attrs = node.setdefault("attrs", {})
                    object_key = attrs.get("objectKey") or self._file_storage.extract_object_key(
                        attrs.get("src"),
                        allowed_prefixes=["news/"],
                    )
                    if object_key:
                        file_url = await self._file_storage.get_file_url(object_key)
                        attrs["src"] = file_url or object_key
                        attrs["objectKey"] = object_key

                for value in node.values():
                    await hydrate_node(value)
            elif isinstance(node, list):
                for item in node:
                    await hydrate_node(item)

        await hydrate_node(hydrated_body)
        return hydrated_body


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
