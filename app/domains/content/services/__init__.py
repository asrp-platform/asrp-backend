from typing import Annotated

from fastapi import Depends

from app.domains.content.services.news_service import NewsDTO, NewsService


NewsServiceDep = Annotated[NewsService, Depends()]

__all__ = ["NewsDTO", "NewsService", "NewsServiceDep"]
