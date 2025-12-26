from fastapi import APIRouter

from app.domains.directors_board.schemas import BoardMemberSchema, CreateBoardMemberSchema
from app.domains.directors_board.services import DirectorBoardMemberServiceDep
from app.domains.shared.deps import AdminUserDep

router = APIRouter(tags=["Admin: Directors board"])


@router.get("/")
async def get_all_director_members(director_service: DirectorBoardMemberServiceDep) -> list[BoardMemberSchema]:
    data, count = await director_service.get_all_directors()
    return [BoardMemberSchema.from_orm(permission) for permission in data]


@router.post("/")
async def create_director_member(
    data: CreateBoardMemberSchema,
    admin: AdminUserDep,  # noqa Auth dep
    director_service: DirectorBoardMemberServiceDep,
) -> BoardMemberSchema:
    director = await director_service.create_director(**data.model_dump())
    return BoardMemberSchema.from_orm(director)
