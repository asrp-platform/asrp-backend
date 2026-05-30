from fastapi import APIRouter

from app.domains.directors_board.schemas import BoardMemberSchema
from app.domains.directors_board.use_cases.get_directors_board_members import GetDirectorsBoardMembersUseCaseDep

router = APIRouter(prefix="/directors-board", tags=["Directors board"])


@router.get("", summary="View all directors board members")
async def get_all_director_members(
    use_case: GetDirectorsBoardMembersUseCaseDep,
) -> list[BoardMemberSchema]:
    data, count = await use_case.execute()
    return data
