from typing import Annotated, Any

from fastapi import Depends

from app.domains.news.exceptions import NewsNotFoundError
from app.domains.news.models import News
from app.domains.shared.transaction_managers import TransactionManagerDep


class NewsService:
    def __init__(self, transaction_manager):
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
                raise NewsNotFoundError("News with provided ID not found")
            await self.transaction_manager.news_repository.update(news_id, **update_data)

    async def get_news_by_id(self, news_id: int) -> News:
        async with self.transaction_manager:
            news = await self.transaction_manager.news_repository.get_first_by_kwargs(id=news_id)
            if news is None:
                raise NewsNotFoundError("News with provided ID not found")
            return news

    async def set_news_deleted(self, news_id):
        async with self.transaction_manager:
            news = await self.transaction_manager.news_repository.get_first_by_kwargs(id=news_id)
            if news is None:
                raise NewsNotFoundError("News with provided ID not found")
            await self.transaction_manager.news_repository.update(news_id, is_deleted=True)


def get_news_service(
    transaction_manager: TransactionManagerDep,
) -> NewsService:
    return NewsService(transaction_manager)


NewsServiceDep = Annotated[NewsService, Depends(get_news_service)]
