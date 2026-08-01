from pathlib import Path
from typing import Annotated, Any

from fastapi import Depends

from app.core.common.exceptions import InvalidMimeTypeError, NotFoundError
from app.core.utils.save_file import save_file
from app.domains.news.models import News, Webinar
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
        if open_transaction:
            async with self._tm:
                return await self._tm.webinar_repository.list(limit, offset, order_by, filters)

        return await self._tm.webinar_repository.list(limit, offset, order_by, filters)

    async def create_webinar(self, *, open_transaction=False, **kwargs) -> Webinar:
        if open_transaction:
            async with self._tm:
                return await self._tm.webinar_repository.create(**kwargs)

        return await self._tm.webinar_repository.create(**kwargs)


NewsServiceDep = Annotated[NewsService, Depends()]
WebinarServiceDep = Annotated[WebinarsService, Depends()]
