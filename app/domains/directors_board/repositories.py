from app.core.database.base_repository import SQLAlchemyRepository
from app.domains.directors_board.models import DirectorBoardMember


class DirectorBoardMemberRepository(SQLAlchemyRepository):
    model = DirectorBoardMember
