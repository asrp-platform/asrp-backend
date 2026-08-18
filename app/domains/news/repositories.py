from sqlalchemy import asc, desc, func, select

from app.core.database.base_repository import InvalidOrderAttributeError, SQLAlchemyRepository
from app.domains.news.models import News, Webinar, WebinarRegisteredUsers
from app.domains.users.models import User


class NewsRepository(SQLAlchemyRepository):
    model = News


class WebinarRepository(SQLAlchemyRepository):
    model = Webinar

    async def list_registered_users(
        self,
        webinar_id: int,
        *,
        limit: int | None = None,
        offset: int | None = None,
        order_by: str | None = None,
    ) -> tuple[list[User], int]:
        conditions = (
            WebinarRegisteredUsers.webinar_id == webinar_id,
            User._deleted.is_(False),
        )
        stmt = select(User).join(WebinarRegisteredUsers, WebinarRegisteredUsers.user_id == User.id).where(*conditions)
        count_stmt = (
            select(func.count(User.id))
            .join(WebinarRegisteredUsers, WebinarRegisteredUsers.user_id == User.id)
            .where(*conditions)
        )

        for param in order_by.split(",") if order_by else ["id"]:
            descending = param.startswith("-")
            field_name = param.removeprefix("-")
            if not hasattr(User, field_name):
                raise InvalidOrderAttributeError(f"User doesn't have attribute <{param}>")
            field = getattr(User, field_name)
            stmt = stmt.order_by(desc(field) if descending else asc(field))

        if limit is not None:
            stmt = stmt.limit(limit)
        if offset is not None:
            stmt = stmt.offset(offset)

        users = list((await self.session.execute(stmt)).scalars().all())
        count = (await self.session.execute(count_stmt)).scalar_one()
        return users, count
