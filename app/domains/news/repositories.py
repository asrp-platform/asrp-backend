from app.core.database.base_repository import SQLAlchemyRepository
from app.domains.news.models import News, Webinar


class NewsRepository(SQLAlchemyRepository):
    model = News


class WebinarRepository(SQLAlchemyRepository):
    model = Webinar
