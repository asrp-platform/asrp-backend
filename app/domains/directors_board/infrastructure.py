from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database.base_repository import SQLAlchemyRepository
from app.core.database.setup_db import session_getter
from app.core.database.unit_of_work import SQLAlchemyUnitOfWork
from app.domains.directors_board.models import DirectorBoardMember


class DirectorBoardMemberRepository(SQLAlchemyRepository):
    model = DirectorBoardMember

    async def get_max_order(self) -> int:
        from sqlalchemy import func, select
        stmt = select(func.coalesce(func.max(self.model.order), 0))
        return (await self.session.execute(stmt)).scalar_one_or_none() or 0


class DirectorsBoardMemberUnitOfWork(SQLAlchemyUnitOfWork):
    def __init__(self, session=None):
        super().__init__(session)
        self.director_board_member_repository = DirectorBoardMemberRepository(self._session)


def get_director_board_member_unit_of_work(
    session: Annotated[AsyncSession, Depends(session_getter)],
) -> DirectorsBoardMemberUnitOfWork:
    return DirectorsBoardMemberUnitOfWork(session)
