from copy import deepcopy
from typing import Annotated, Any

from fastapi import Depends
from loguru import logger

from app.core.storage.base_storage import BaseFileStorage
from app.core.storage.storage_factory import FileStorageDep
from app.domains.content.models import CaseOfTheMonth
from app.domains.content.schemas import CaseOfTheMonthSchema, CaseTagSchema


class CaseOfTheMonthService:
    MAX_IMAGE_SIZE = 5 * 1024 * 1024
    ALLOWED_IMAGE_CONTENT_TYPES = {"image/jpeg", "image/png", "image/webp", "image/gif"}
    IMAGE_PREFIX = "case-of-the-month/"

    def __init__(self, file_storage: BaseFileStorage):
        self._file_storage = file_storage

    def normalize_image_key(self, value: str | None) -> str | None:
        if value is None:
            return None
        return self._file_storage.extract_object_key(value, allowed_prefixes=[self.IMAGE_PREFIX]) or value

    def get_case_image_keys(self, case: CaseOfTheMonth) -> set[str]:
        keys: set[str] = set()

        if case.cover_key and case.cover_key.startswith(self.IMAGE_PREFIX):
            keys.add(case.cover_key)

        for content in (case.history, case.case_findings, case.answer):
            keys.update(self.extract_content_image_keys(content))

        for slide in case.virtual_slides:
            object_key = self._file_storage.extract_object_key(
                slide,
                allowed_prefixes=[self.IMAGE_PREFIX],
            )
            if object_key:
                keys.add(object_key)

        return keys

    def extract_content_image_keys(self, content: dict) -> set[str]:
        keys: set[str] = set()

        def collect(node: Any) -> None:
            if isinstance(node, dict):
                if node.get("type") == "image":
                    attrs = node.get("attrs") or {}
                    object_key = attrs.get("objectKey") or self._file_storage.extract_object_key(
                        attrs.get("src"),
                        allowed_prefixes=[self.IMAGE_PREFIX],
                    )
                    if isinstance(object_key, str) and object_key.startswith(self.IMAGE_PREFIX):
                        keys.add(object_key)
                for value in node.values():
                    collect(value)
            elif isinstance(node, list):
                for item in node:
                    collect(item)

        collect(content)
        return keys

    def normalize_content_image_keys(self, content: dict) -> dict:
        normalized_content = deepcopy(content)

        def normalize_node(node: Any) -> None:
            if isinstance(node, dict):
                if node.get("type") == "image":
                    attrs = node.setdefault("attrs", {})
                    object_key = attrs.get("objectKey") or self._file_storage.extract_object_key(
                        attrs.get("src"),
                        allowed_prefixes=[self.IMAGE_PREFIX],
                    )
                    if object_key:
                        attrs["src"] = object_key
                        attrs["objectKey"] = object_key

                for value in node.values():
                    normalize_node(value)
            elif isinstance(node, list):
                for item in node:
                    normalize_node(item)

        normalize_node(normalized_content)
        return normalized_content

    async def hydrate_content_image_urls(self, content: dict) -> dict:
        hydrated_content = deepcopy(content)

        async def hydrate_node(node: Any) -> None:
            if isinstance(node, dict):
                if node.get("type") == "image":
                    attrs = node.setdefault("attrs", {})
                    object_key = attrs.get("objectKey") or self._file_storage.extract_object_key(
                        attrs.get("src"),
                        allowed_prefixes=[self.IMAGE_PREFIX],
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

        await hydrate_node(hydrated_content)
        return hydrated_content

    async def hydrate_virtual_slides(self, slides: list[str]) -> list[str]:
        hydrated_slides: list[str] = []
        for slide in slides:
            object_key = self._file_storage.extract_object_key(
                slide,
                allowed_prefixes=[self.IMAGE_PREFIX],
            )
            if object_key:
                hydrated_slides.append(await self._file_storage.get_file_url(object_key) or object_key)
            else:
                hydrated_slides.append(slide)
        return hydrated_slides

    async def delete_image_keys(self, object_keys: set[str]) -> None:
        for object_key in object_keys:
            try:
                await self._file_storage.delete_file(object_key)
            except Exception:
                logger.exception("Failed to remove orphaned case of the month image %s", object_key)

    async def to_dtos(self, cases: list[CaseOfTheMonth]) -> list[CaseOfTheMonthSchema]:
        return [await self.to_dto(case) for case in cases]

    async def to_dto(self, case: CaseOfTheMonth) -> CaseOfTheMonthSchema:
        cover_url = None
        if case.cover_key:
            cover_url = await self._file_storage.get_file_url(case.cover_key)

        return CaseOfTheMonthSchema(
            id=case.id,
            created_at=case.created_at,
            updated_at=case.updated_at,
            title=case.title,
            slug=case.slug,
            cover_key=case.cover_key,
            cover_url=cover_url,
            history=await self.hydrate_content_image_urls(case.history),
            case_findings=await self.hydrate_content_image_urls(case.case_findings),
            virtual_slides=await self.hydrate_virtual_slides(case.virtual_slides),
            questions=case.questions,
            publication_month=case.publication_month,
            answer=await self.hydrate_content_image_urls(case.answer),
            tags=[CaseTagSchema.model_validate(tag) for tag in case.tags],
        )


def get_case_of_the_month_service(file_storage: FileStorageDep) -> CaseOfTheMonthService:
    return CaseOfTheMonthService(file_storage)


CaseOfTheMonthServiceDep = Annotated[
    CaseOfTheMonthService,
    Depends(get_case_of_the_month_service),
]
