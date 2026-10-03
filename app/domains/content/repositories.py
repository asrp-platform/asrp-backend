from collections.abc import Iterable, Sequence

from sqlalchemy import func, select

from app.core.database.base_repository import SQLAlchemyRepository
from app.domains.content.models import CaseOfTheMonth, CaseOfTheMonthTag, CaseTag, News, Webinar


class NewsRepository(SQLAlchemyRepository):
    model = News


class CaseOfTheMonthRepository(SQLAlchemyRepository):
    model = CaseOfTheMonth


class CaseTagRepository(SQLAlchemyRepository):
    model = CaseTag

    async def has_active_cases(self, tag_id: int) -> bool:
        statement = (
            select(func.count(CaseOfTheMonth.id))
            .join(CaseOfTheMonthTag, CaseOfTheMonthTag.case_id == CaseOfTheMonth.id)
            .where(
                CaseOfTheMonthTag.tag_id == tag_id,
                CaseOfTheMonthTag._deleted.is_(False),
                CaseOfTheMonth._deleted.is_(False),
            )
        )
        return (await self.session.execute(statement)).scalar_one() > 0

    async def get_by_ids(self, tag_ids: Iterable[int]) -> Sequence[CaseTag]:
        tag_ids = list(dict.fromkeys(tag_ids))
        if not tag_ids:
            return []

        statement = select(CaseTag).where(CaseTag.id.in_(tag_ids), CaseTag._deleted.is_(False))
        return (await self.session.execute(statement)).scalars().all()


class WebinarRepository(SQLAlchemyRepository):
    model = Webinar
