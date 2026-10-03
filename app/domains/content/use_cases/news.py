from typing import Annotated, Any

from fastapi import Depends

from app.core.common.exceptions import InvalidMimeTypeError, NotFoundError, PayloadTooLargeError
from app.core.common.responses import PaginatedResponse
from app.core.storage.storage_factory import FileStorageDep
from app.core.utils.permissions import check_any_permission, check_permissions
from app.core.utils.save_file import generate_filename
from app.domains.content.cache import NewsCacheDep
from app.domains.content.schemas import NewsSchema
from app.domains.content.services import NewsServiceDep
from app.domains.shared.transaction_managers import TransactionManagerDep
from app.domains.shared.types import FileData, StoredFile


class GetNewsListUseCase:
    def __init__(self, transaction_manager: TransactionManagerDep, service: NewsServiceDep):
        self.__tm = transaction_manager
        self.__service = service

    async def execute(
        self, permissions: list[str] | None, *, limit: int, offset: int, order_by: str | None, filters: dict[str, Any]
    ):
        if permissions is not None:
            check_permissions("news.view", permissions)
        async with self.__tm:
            news, count = await self.__tm.news_repository.list(limit, offset, order_by, filters)
            return await self.__service.to_dtos(news), count


class GetPublishedNewsListUseCase:
    def __init__(self, transaction_manager: TransactionManagerDep, service: NewsServiceDep, cache: NewsCacheDep):
        self.__tm = transaction_manager
        self.__service = service
        self.__cache = cache

    async def execute(
        self, *, page: int, page_size: int, limit: int, offset: int, order_by: str | None, filters: dict[str, Any]
    ):
        use_cache = page == 1 and page_size == 8 and order_by in (None, "-created_at") and not filters
        if use_cache:
            cached_data = await self.__cache.get_first_page_from_cache()
            if cached_data is not None:
                return cached_data

        filters = {**filters, "is_published": True}
        async with self.__tm:
            news, count = await self.__tm.news_repository.list(limit, offset, order_by, filters)
            data = await self.__service.to_dtos(news)
        response = PaginatedResponse[NewsSchema](count=count, data=data, page=page, page_size=page_size)
        if use_cache:
            await self.__cache.cache_first_page(response)
        return response


class GetNewsByIdUseCase:
    def __init__(self, transaction_manager: TransactionManagerDep, service: NewsServiceDep):
        self.__tm = transaction_manager
        self.__service = service

    async def execute(self, permissions: list[str], news_id: int):
        check_permissions("news.view", permissions)
        async with self.__tm:
            news = await self.__tm.news_repository.get_first_by_kwargs(id=news_id)
            if news is None:
                raise NotFoundError("News with provided ID not found")
            return await self.__service.to_dto(news)


class GetPublishedNewsBySlugUseCase:
    def __init__(self, transaction_manager: TransactionManagerDep, service: NewsServiceDep):
        self.__tm = transaction_manager
        self.__service = service

    async def execute(self, slug: str):
        async with self.__tm:
            news = await self.__tm.news_repository.get_first_by_kwargs(slug=slug, is_published=True)
            if news is None:
                raise NotFoundError("News with provided slug not found")
            return await self.__service.to_dto(news)


class CreateNewsUseCase:
    def __init__(self, transaction_manager: TransactionManagerDep, service: NewsServiceDep, cache: NewsCacheDep):
        self.__tm = transaction_manager
        self.__service = service
        self.__cache = cache

    async def execute(self, permissions: list[str], author_id: int, data: dict[str, Any]):
        check_permissions("news.create", permissions)
        if body := data.get("body"):
            data["body"] = self.__service.normalize_body_image_keys(body)
        async with self.__tm:
            news = await self.__tm.news_repository.create(**data, author_id=author_id)
            await self.__tm.flush()
            news = await self.__service.to_dto(news)
        await self.__cache.invalidate_first_page()
        return news


class UpdateNewsUseCase:
    def __init__(self, transaction_manager: TransactionManagerDep, service: NewsServiceDep, cache: NewsCacheDep):
        self.__tm = transaction_manager
        self.__service = service
        self.__cache = cache

    async def execute(self, permissions: list[str], news_id: int, data: dict[str, Any]):
        check_permissions("news.update", permissions)
        if body := data.get("body"):
            data["body"] = self.__service.normalize_body_image_keys(body)
        async with self.__tm:
            existing_news = await self.__tm.news_repository.get_first_by_kwargs(id=news_id)
            if existing_news is None:
                raise NotFoundError("News with provided ID not found")
            old_image_keys = self.__service.get_news_image_keys(existing_news)
            news = await self.__tm.news_repository.update(news_id, **data)
            await self.__tm.flush()
            new_image_keys = self.__service.get_news_image_keys(news)
            news = await self.__service.to_dto(news)
        await self.__service.delete_image_keys(old_image_keys - new_image_keys)
        await self.__cache.invalidate_first_page()
        return news


class DeleteNewsUseCase:
    def __init__(self, transaction_manager: TransactionManagerDep, service: NewsServiceDep, cache: NewsCacheDep):
        self.__tm = transaction_manager
        self.__service = service
        self.__cache = cache

    async def execute(self, permissions: list[str], news_id: int):
        check_permissions("news.delete", permissions)
        async with self.__tm:
            news = await self.__tm.news_repository.get_first_by_kwargs(id=news_id)
            if news is None:
                raise NotFoundError("News with provided ID not found")
            image_keys = self.__service.get_news_image_keys(news)
            result = await self.__tm.news_repository.mark_as_deleted(row_id=news_id)
        await self.__service.delete_image_keys(image_keys)
        await self.__cache.invalidate_first_page()
        return result


class UploadNewsImageUseCase:
    def __init__(self, file_storage: FileStorageDep, service: NewsServiceDep):
        self.__file_storage = file_storage
        self.__service = service

    async def execute(self, permissions: list[str], file_data: FileData):
        check_any_permission({"news.create", "news.update"}, permissions)
        if file_data.content_type not in self.__service.ALLOWED_IMAGE_CONTENT_TYPES:
            raise InvalidMimeTypeError("Invalid image content type")
        if len(file_data.content) > self.__service.MAX_IMAGE_SIZE:
            raise PayloadTooLargeError("Image must be smaller than 5 MB")
        filename = generate_filename(file_data.filename, prefix="news")
        stored_file = await self.__file_storage.upload_file(object_key=filename, file_content=file_data.content)
        file_url = await self.__file_storage.get_file_url(stored_file.object_key)
        return StoredFile(file_url=file_url, object_key=stored_file.object_key)


GetNewsListUseCaseDep = Annotated[GetNewsListUseCase, Depends(GetNewsListUseCase)]
GetPublishedNewsListUseCaseDep = Annotated[GetPublishedNewsListUseCase, Depends(GetPublishedNewsListUseCase)]
GetNewsByIdUseCaseDep = Annotated[GetNewsByIdUseCase, Depends(GetNewsByIdUseCase)]
GetPublishedNewsBySlugUseCaseDep = Annotated[GetPublishedNewsBySlugUseCase, Depends(GetPublishedNewsBySlugUseCase)]
CreateNewsUseCaseDep = Annotated[CreateNewsUseCase, Depends(CreateNewsUseCase)]
UpdateNewsUseCaseDep = Annotated[UpdateNewsUseCase, Depends(UpdateNewsUseCase)]
DeleteNewsUseCaseDep = Annotated[DeleteNewsUseCase, Depends(DeleteNewsUseCase)]
UploadNewsImageUseCaseDep = Annotated[UploadNewsImageUseCase, Depends(UploadNewsImageUseCase)]
