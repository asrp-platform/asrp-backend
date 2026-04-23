from app.core.database.base_repository import SQLAlchemyRepository
from app.domains.news.models import News


class NewsRepository(SQLAlchemyRepository):
    model = News
