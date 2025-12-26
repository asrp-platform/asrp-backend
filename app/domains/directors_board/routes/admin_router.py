from fastapi import APIRouter

from app.domains.directors_board.schemas import BoardMemberSchema, CreateBoardMemberSchema
from app.domains.directors_board.services import DirectorBoardMemberServiceDep
from app.domains.shared.deps import AdminUserDep, UserPermissionsDep
from app.domains.shared.exceptions import PermissionsResponses

router = APIRouter(prefix="/director_board", tags=["Admin: Directors board"])


class ViewDirectorResponses(PermissionsResponses):
    pass


@router.get("", responses=ViewDirectorResponses.responses, summary="View all directors board (admin view)")
async def get_all_director_members(
    director_service: DirectorBoardMemberServiceDep,
    admin: AdminUserDep,  # noqa Auth dep
    permissions: UserPermissionsDep,
) -> list[BoardMemberSchema]:
    if "director_board.view" not in permissions:
        raise ViewDirectorResponses.PERMISSION_ERROR
    data, count = await director_service.get_all_directors()
    return [BoardMemberSchema.from_orm(permission) for permission in data]


class CreateDirectorResponses(PermissionsResponses):
    pass


@router.post(
    "",
    responses=CreateDirectorResponses.responses,
    summary="Create a director board member",
)
async def create_director_member(
    data: CreateBoardMemberSchema,
    admin: AdminUserDep,  # noqa Auth dep
    permissions: UserPermissionsDep,
    director_service: DirectorBoardMemberServiceDep,
) -> BoardMemberSchema:
    if "director_board.create" not in permissions:
        raise CreateDirectorResponses.PERMISSION_ERROR
    director = await director_service.create_director(**data.model_dump())
    return BoardMemberSchema.from_orm(director)
