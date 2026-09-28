from typing import Annotated, Any

from fastapi import Depends
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.core.common.exceptions import InvalidMimeTypeError, NotFoundError, PayloadTooLargeError
from app.core.storage.storage_factory import FileStorageDep
from app.core.utils.save_file import generate_filename
from app.domains.content.models import CaseOfTheMonth, CaseTag
from app.domains.content.schemas import CaseOfTheMonthSchema
from app.domains.content.services.case_of_the_month_service import (
    CaseOfTheMonthService,
    CaseOfTheMonthServiceDep,
)
from app.domains.shared.transaction_managers import TransactionManagerDep
from app.domains.shared.types import FileData, StoredFile


_UNSET = object()


def _case_with_tags_statement():
    return select(CaseOfTheMonth).options(selectinload(CaseOfTheMonth.tags))


async def _get_case_tags(transaction_manager, tag_ids: list[int]):
    tags = list(await transaction_manager.case_tag_repository.get_by_ids(tag_ids))
    found_ids = {tag.id for tag in tags}
    missing_ids = [tag_id for tag_id in dict.fromkeys(tag_ids) if tag_id not in found_ids]
    if missing_ids:
        missing_ids_text = ", ".join(str(tag_id) for tag_id in missing_ids)
        raise NotFoundError(f"Case tag(s) with provided ID not found: {missing_ids_text}")
    return tags


def _normalize_case_data(data: dict[str, Any], service: CaseOfTheMonthService) -> dict[str, Any]:
    normalized_data = data.copy()

    if "cover_key" in normalized_data:
        normalized_data["cover_key"] = service.normalize_image_key(normalized_data["cover_key"])

    for field_name in ("history", "case_findings", "answer"):
        if field_name in normalized_data and normalized_data[field_name] is not None:
            normalized_data[field_name] = service.normalize_content_image_keys(normalized_data[field_name])

    if "virtual_slides" in normalized_data and normalized_data["virtual_slides"] is not None:
        normalized_data["virtual_slides"] = [
            service.normalize_image_key(slide) or slide for slide in normalized_data["virtual_slides"]
        ]

    return normalized_data


class GetCaseOfTheMonthListUseCase:
    def __init__(self, transaction_manager: TransactionManagerDep, service: CaseOfTheMonthServiceDep):
        self.__tm = transaction_manager
        self.__service = service

    async def execute(self, *, limit: int, offset: int, order_by: str | None, filters: dict[str, Any] | None = None):
        async with self.__tm:
            order_by = order_by or "-publication_month,-id"
            tag_id = (filters or {}).get("tag_id")
            stmt = _case_with_tags_statement()
            if tag_id is not None:
                stmt = stmt.where(CaseOfTheMonth.tags.any(CaseTag.id == tag_id))
            cases, count = await self.__tm.case_of_the_month_repository.list(
                limit,
                offset,
                order_by,
                stmt=stmt,
            )
            return await self.__service.to_dtos(cases), count


class GetCaseOfTheMonthUseCase:
    def __init__(self, transaction_manager: TransactionManagerDep, service: CaseOfTheMonthServiceDep):
        self.__tm = transaction_manager
        self.__service = service

    async def execute(self, case_id: int) -> CaseOfTheMonthSchema:
        async with self.__tm:
            case = await self.__tm.case_of_the_month_repository.get_first_by_kwargs(
                stmt=_case_with_tags_statement(),
                id=case_id,
            )
            if case is None:
                raise NotFoundError("Case of the month with provided ID not found")
            return await self.__service.to_dto(case)


class CreateCaseOfTheMonthUseCase:
    def __init__(self, transaction_manager: TransactionManagerDep, service: CaseOfTheMonthServiceDep):
        self.__tm = transaction_manager
        self.__service = service

    async def execute(self, data: dict[str, Any]) -> CaseOfTheMonthSchema:
        data = data.copy()
        tag_ids = data.pop("tag_ids", [])
        tag_ids = tag_ids or []
        data = _normalize_case_data(data, self.__service)

        async with self.__tm:
            tags = await _get_case_tags(self.__tm, tag_ids)
            case = await self.__tm.case_of_the_month_repository.create(**data)
            case.tags = tags
            await self.__tm.flush()
            return await self.__service.to_dto(case)


class UpdateCaseOfTheMonthUseCase:
    def __init__(self, transaction_manager: TransactionManagerDep, service: CaseOfTheMonthServiceDep):
        self.__tm = transaction_manager
        self.__service = service

    async def execute(self, case_id: int, data: dict[str, Any]) -> CaseOfTheMonthSchema:
        data = data.copy()
        tag_ids = data.pop("tag_ids", _UNSET)
        data = _normalize_case_data(data, self.__service)

        async with self.__tm:
            case = await self.__tm.case_of_the_month_repository.get_first_by_kwargs(
                stmt=_case_with_tags_statement(),
                id=case_id,
            )
            if case is None:
                raise NotFoundError("Case of the month with provided ID not found")

            old_image_keys = self.__service.get_case_image_keys(case)
            updated_case = case
            if data:
                updated_case = await self.__tm.case_of_the_month_repository.update(case_id, **data)

            if tag_ids is not _UNSET:
                updated_case.tags = await _get_case_tags(self.__tm, tag_ids or [])

            await self.__tm.flush()
            response = await self.__service.to_dto(updated_case)
            new_image_keys = self.__service.get_case_image_keys(updated_case)

        await self.__service.delete_image_keys(old_image_keys - new_image_keys)
        return response


class DeleteCaseOfTheMonthUseCase:
    def __init__(self, transaction_manager: TransactionManagerDep, service: CaseOfTheMonthServiceDep):
        self.__tm = transaction_manager
        self.__service = service

    async def execute(self, case_id: int) -> None:
        async with self.__tm:
            case = await self.__tm.case_of_the_month_repository.get_first_by_kwargs(
                stmt=_case_with_tags_statement(),
                id=case_id,
            )
            if case is None:
                raise NotFoundError("Case of the month with provided ID not found")

            image_keys = self.__service.get_case_image_keys(case)
            await self.__tm.case_of_the_month_repository.mark_as_deleted(case_id)

        await self.__service.delete_image_keys(image_keys)


class UploadCaseOfTheMonthImageUseCase:
    def __init__(self, file_storage: FileStorageDep, service: CaseOfTheMonthServiceDep):
        self.__file_storage = file_storage
        self.__service = service

    async def execute(self, file_data: FileData) -> StoredFile:
        if file_data.content_type not in self.__service.ALLOWED_IMAGE_CONTENT_TYPES:
            raise InvalidMimeTypeError("Invalid image content type")
        if len(file_data.content) > self.__service.MAX_IMAGE_SIZE:
            raise PayloadTooLargeError("Image must be smaller than 5 MB")

        filename = generate_filename(file_data.filename, prefix="case-of-the-month")
        stored_file = await self.__file_storage.upload_file(
            object_key=filename,
            file_content=file_data.content,
            content_type=file_data.content_type,
        )
        file_url = await self.__file_storage.get_file_url(stored_file.object_key)
        return StoredFile(file_url=file_url, object_key=stored_file.object_key)


GetCaseOfTheMonthListUseCaseDep = Annotated[
    GetCaseOfTheMonthListUseCase,
    Depends(GetCaseOfTheMonthListUseCase),
]
GetCaseOfTheMonthUseCaseDep = Annotated[GetCaseOfTheMonthUseCase, Depends(GetCaseOfTheMonthUseCase)]
CreateCaseOfTheMonthUseCaseDep = Annotated[
    CreateCaseOfTheMonthUseCase,
    Depends(CreateCaseOfTheMonthUseCase),
]
UpdateCaseOfTheMonthUseCaseDep = Annotated[
    UpdateCaseOfTheMonthUseCase,
    Depends(UpdateCaseOfTheMonthUseCase),
]
DeleteCaseOfTheMonthUseCaseDep = Annotated[
    DeleteCaseOfTheMonthUseCase,
    Depends(DeleteCaseOfTheMonthUseCase),
]
UploadCaseOfTheMonthImageUseCaseDep = Annotated[
    UploadCaseOfTheMonthImageUseCase,
    Depends(UploadCaseOfTheMonthImageUseCase),
]
