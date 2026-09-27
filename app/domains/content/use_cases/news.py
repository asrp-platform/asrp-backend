from typing import Annotated, Any

from fastapi import Depends

from app.core.common.responses import PaginatedResponse
from app.core.utils.permissions import check_any_permission, check_permissions
from app.domains.content.cache import NewsCacheDep
from app.domains.content.schemas import NewsSchema
from app.domains.content.services import NewsServiceDep
from app.domains.shared.types import FileData


class GetNewsListUseCase:
    def __init__(self, service: NewsServiceDep):
        self.__service = service

    async def execute(
        self, permissions: list[str] | None, *, limit: int, offset: int, order_by: str | None, filters: dict[str, Any]
    ):
        if permissions is not None:
            check_permissions("news.view", permissions)
        return await self.__service.get_news_paginated_counted(
            order_by=order_by, filters=filters, limit=limit, offset=offset, open_transaction=True
        )


class GetPublishedNewsListUseCase:
    def __init__(self, service: NewsServiceDep, cache: NewsCacheDep):
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
        data, count = await self.__service.get_news_paginated_counted(
            order_by=order_by, filters=filters, limit=limit, offset=offset, open_transaction=True
        )
        response = PaginatedResponse[NewsSchema](count=count, data=data, page=page, page_size=page_size)
        if use_cache:
            await self.__cache.cache_first_page(response)
        return response


class GetNewsByIdUseCase:
    def __init__(self, service: NewsServiceDep):
        self.__service = service

    async def execute(self, permissions: list[str], news_id: int):
        check_permissions("news.view", permissions)
        return await self.__service.get_news_by_id(news_id)


class GetPublishedNewsBySlugUseCase:
    def __init__(self, service: NewsServiceDep):
        self.__service = service

    async def execute(self, slug: str):
        return await self.__service.get_published_news_by_slug(slug)


class CreateNewsUseCase:
    def __init__(self, service: NewsServiceDep, cache: NewsCacheDep):
        self.__service = service
        self.__cache = cache

    async def execute(self, permissions: list[str], author_id: int, data: dict[str, Any]):
        check_permissions("news.create", permissions)
        news = await self.__service.create_news(**data, author_id=author_id)
        await self.__cache.invalidate_first_page()
        return news


class UpdateNewsUseCase:
    def __init__(self, service: NewsServiceDep, cache: NewsCacheDep):
        self.__service = service
        self.__cache = cache

    async def execute(self, permissions: list[str], news_id: int, data: dict[str, Any]):
        check_permissions("news.update", permissions)
        news = await self.__service.update_news(news_id, data)
        await self.__cache.invalidate_first_page()
        return news


class DeleteNewsUseCase:
    def __init__(self, service: NewsServiceDep, cache: NewsCacheDep):
        self.__service = service
        self.__cache = cache

    async def execute(self, permissions: list[str], news_id: int):
        check_permissions("news.delete", permissions)
        result = await self.__service.delete_news_by_id(news_id)
        await self.__cache.invalidate_first_page()
        return result


class UploadNewsImageUseCase:
    def __init__(self, service: NewsServiceDep):
        self.__service = service

    async def execute(self, permissions: list[str], file_data: FileData):
        check_any_permission({"news.create", "news.update"}, permissions)
        return await self.__service.upload_image(file_data)


GetNewsListUseCaseDep = Annotated[GetNewsListUseCase, Depends(GetNewsListUseCase)]
GetPublishedNewsListUseCaseDep = Annotated[GetPublishedNewsListUseCase, Depends(GetPublishedNewsListUseCase)]
GetNewsByIdUseCaseDep = Annotated[GetNewsByIdUseCase, Depends(GetNewsByIdUseCase)]
GetPublishedNewsBySlugUseCaseDep = Annotated[GetPublishedNewsBySlugUseCase, Depends(GetPublishedNewsBySlugUseCase)]
CreateNewsUseCaseDep = Annotated[CreateNewsUseCase, Depends(CreateNewsUseCase)]
UpdateNewsUseCaseDep = Annotated[UpdateNewsUseCase, Depends(UpdateNewsUseCase)]
DeleteNewsUseCaseDep = Annotated[DeleteNewsUseCase, Depends(DeleteNewsUseCase)]
UploadNewsImageUseCaseDep = Annotated[UploadNewsImageUseCase, Depends(UploadNewsImageUseCase)]
