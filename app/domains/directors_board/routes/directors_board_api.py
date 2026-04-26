from typing import Annotated

from fastapi import APIRouter, Query

from app.domains.directors_board.schemas import BoardMemberSchema
from app.domains.directors_board.services import DirectorBoardMemberServiceDep
from app.domains.shared.schemas import UploadedImageSchema

router = APIRouter(prefix="/directors-board", tags=["Directors board"])


@router.get("/images")
async def get_directors_board_member_photo(
    object_key: Annotated[str, Query(...)],
    director_service: DirectorBoardMemberServiceDep,
) -> UploadedImageSchema:
    photo_url = await director_service.get_photo_url_by_object_key(object_key)
    return UploadedImageSchema(path=photo_url)


@router.get("", summary="View all directors board (admin view)")
async def get_all_director_members(
    director_service: DirectorBoardMemberServiceDep,
) -> list[BoardMemberSchema]:
    data, count = await director_service.get_directors_board_members()
    return data
