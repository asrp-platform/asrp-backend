from copy import deepcopy
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from loguru import logger

from app.core.common.exceptions import InvalidMimeTypeError, NotFoundError, PayloadTooLargeError
from app.core.storage.storage_factory import FileStorageDep
from app.core.utils.save_file import generate_filename
from app.domains.content.models import News
from app.domains.shared.transaction_managers import TransactionManagerDep
from app.domains.shared.types import FileData, StoredFile


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
