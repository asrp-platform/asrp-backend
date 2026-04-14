from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database.base_repository import SQLAlchemyRepository
from app.core.database.base_transaction_manager import SQLAlchemyTransactionManagerBase
from app.core.database.setup_db import session_getter
from app.domains.directors_board.models import DirectorBoardMember


class DirectorBoardMemberRepository(SQLAlchemyRepository):
    model = DirectorBoardMember


class DirectorsBoardMemberTransactionManagerBase(SQLAlchemyTransactionManagerBase):
    def __init__(self, session=None):
        super().__init__(session)
        self.director_board_member_repository = DirectorBoardMemberRepository(self._session)


def get_director_board_member_unit_of_work(
    session: Annotated[AsyncSession, Depends(session_getter)],
) -> DirectorsBoardMemberTransactionManagerBase:
    return DirectorsBoardMemberTransactionManagerBase(session)
