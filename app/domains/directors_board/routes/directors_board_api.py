from fastapi import APIRouter

from app.domains.directors_board.schemas import BoardMemberSchema
from app.domains.directors_board.services import DirectorBoardMemberServiceDep

router = APIRouter(prefix="/directors-board", tags=["Directors board"])


@router.get("", summary="View all directors board members")
async def get_all_director_members(
    director_service: DirectorBoardMemberServiceDep,
) -> list[BoardMemberSchema]:
    data, count = await director_service.get_directors_board_members()
    return data
