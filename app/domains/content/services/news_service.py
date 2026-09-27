from copy import deepcopy
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from loguru import logger

from app.core.storage.storage_factory import FileStorageDep
from app.domains.content.models import News
from app.domains.shared.transaction_managers import TransactionManagerDep


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

    def get_news_image_keys(self, news: News) -> set[str]:
        keys = self.extract_body_image_keys(news.body)
        if news.cover_key and news.cover_key.startswith("news/"):
            keys.add(news.cover_key)
        return keys

    def extract_body_image_keys(self, body: dict) -> set[str]:
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

    async def delete_image_keys(self, object_keys: set[str]) -> None:
        for object_key in object_keys:
            try:
                await self._file_storage.delete_file(object_key)
            except Exception:
                logger.exception("Failed to remove orphaned news image %s", object_key)

    async def to_dtos(self, news: list[News]) -> list[NewsDTO]:
        return [await self.to_dto(item) for item in news]

    async def to_dto(self, news: News) -> NewsDTO:
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
            body=await self.hydrate_body_image_urls(news.body),
            when=news.when,
            where=news.where,
            is_published=news.is_published,
            author_id=news.author_id,
        )

    def normalize_body_image_keys(self, body: dict) -> dict:
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

    async def hydrate_body_image_urls(self, body: dict) -> dict:
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
