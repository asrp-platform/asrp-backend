from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database.base_repository import SQLAlchemyRepository
from app.core.database.setup_db import session_getter
from app.core.database.unit_of_work import SQLAlchemyUnitOfWork
from app.domains.directors_board.models import DirectorBoardMember


class DirectorBoardMemberRepository(SQLAlchemyRepository):
    model = DirectorBoardMember


class DirectorBoardMemberUnitOfWork(SQLAlchemyUnitOfWork):
    def __init__(self, session=None):
        super().__init__(session)
        self.director_board_member_repository = DirectorBoardMemberRepository(self._session)


def get_director_board_member_unit_of_work(
    session: Annotated[AsyncSession, Depends(session_getter)],
) -> DirectorBoardMemberUnitOfWork:
    return DirectorBoardMemberUnitOfWork(session)
