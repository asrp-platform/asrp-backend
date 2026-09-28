from collections.abc import Iterable, Sequence

from sqlalchemy import select

from app.core.database.base_repository import SQLAlchemyRepository
from app.domains.content.models import CaseOfTheMonth, CaseTag, News, Webinar


class NewsRepository(SQLAlchemyRepository):
    model = News


class CaseOfTheMonthRepository(SQLAlchemyRepository):
    model = CaseOfTheMonth


class CaseTagRepository(SQLAlchemyRepository):
    model = CaseTag

    async def get_by_ids(self, tag_ids: Iterable[int]) -> Sequence[CaseTag]:
        tag_ids = list(dict.fromkeys(tag_ids))
        if not tag_ids:
            return []

        statement = select(CaseTag).where(CaseTag.id.in_(tag_ids), CaseTag._deleted.is_(False))
        return (await self.session.execute(statement)).scalars().all()


class WebinarRepository(SQLAlchemyRepository):
    model = Webinar
