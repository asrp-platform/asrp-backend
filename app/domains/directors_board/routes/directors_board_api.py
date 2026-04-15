from fastapi import APIRouter

from app.domains.directors_board.schemas import BoardMemberSchema
from app.domains.directors_board.use_cases.get_directors_list import GetDirectorsListUseCaseDep

router = APIRouter(prefix="/directors-board", tags=["Directors board"])


@router.get("", summary="View all directors board (admin view)")
async def get_all_director_members(
    use_case: GetDirectorsListUseCaseDep,
) -> list[BoardMemberSchema]:
    return await use_case.execute()
