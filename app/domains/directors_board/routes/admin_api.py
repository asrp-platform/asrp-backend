from typing import Annotated

from fastapi import APIRouter, File, Path, UploadFile

from app.core.common.responses import PermissionsResponses
from app.core.config import settings
from app.core.utils.save_file import save_file
from app.domains.directors_board.exceptions import DirectionBoardMemberNotFoundError, InvalidReorderItemsCountError
from app.domains.directors_board.schemas import (
    BoardMemberSchema,
    CardOrderUpdate,
    CreateBoardMemberSchema,
    UpdateBoardMemberSchema,
)
from app.domains.directors_board.services import DirectorBoardMemberServiceDep
from app.domains.shared.deps import AdminPermissionsDep, AdminUserDep

router = APIRouter(prefix="/directors-board", tags=["Admin: Directors board"])


class ViewDirectorResponses(PermissionsResponses):
    pass


@router.get("", responses=ViewDirectorResponses.responses, summary="View all directors board (admin view)")
async def get_all_director_members(
    director_service: DirectorBoardMemberServiceDep,
    admin: AdminUserDep,  # noqa Auth dep
    permissions: AdminPermissionsDep,
) -> list[BoardMemberSchema]:
    if "director_board.view" not in permissions:
        raise ViewDirectorResponses.PERMISSION_ERROR
    data, count = await director_service.get_all_directors()
    return [BoardMemberSchema.from_orm(permission) for permission in data]


class CreateDirectorResponses(PermissionsResponses):
    pass


@router.post(
    "",
    status_code=201,
    responses=CreateDirectorResponses.responses,
    summary="Create a director board member",
)
async def create_director_member(
    data: CreateBoardMemberSchema,
    admin: AdminUserDep,  # noqa auth dep
    permissions: AdminPermissionsDep,
    director_service: DirectorBoardMemberServiceDep,
) -> BoardMemberSchema:
    if "director_board.create" not in permissions:
        raise CreateDirectorResponses.PERMISSION_ERROR
    director = await director_service.create_director_member(**data.model_dump())
    return BoardMemberSchema.from_orm(director)


class UpdateDirectorMemberResponses(PermissionsResponses):
    DIRECTOR_MEMBER_NOT_FOUND = 404, "Director member with provided ID not found"


@router.patch(
    "/{director_member_id}",
    responses=UpdateDirectorMemberResponses.responses,
    summary="Update a director board member",
)
async def update_director_member(
    director_member_id: Annotated[int, Path(...)],
    admin: AdminUserDep,  # noqa auth dep
    permissions: AdminPermissionsDep,
    director_service: DirectorBoardMemberServiceDep,
    update_data: UpdateBoardMemberSchema,
) -> BoardMemberSchema:
    if "director_board.update" not in permissions:
        raise UpdateDirectorMemberResponses.PERMISSION_ERROR
    try:
        update_data_dict = update_data.model_dump(exclude_unset=True)
        updated_director_member = await director_service.update_director_member(director_member_id, update_data_dict)
        return BoardMemberSchema.from_orm(updated_director_member)

    except DirectionBoardMemberNotFoundError:
        raise UpdateDirectorMemberResponses.DIRECTOR_MEMBER_NOT_FOUND


class DeleteDirectorMemberResponses(PermissionsResponses):
    DIRECTOR_MEMBER_NOT_FOUND = 404, "Director member with provided ID not found"


@router.delete(
    "/{director_member_id}",
    responses=DeleteDirectorMemberResponses.responses,
    summary="Delete a director board member",
)
async def delete_director_member(
    director_member_id: Annotated[int, Path(...)],
    admin: AdminUserDep,  # noqa auth dep
    permissions: AdminPermissionsDep,
    director_service: DirectorBoardMemberServiceDep,
) -> int:
    if "director_board.delete" not in permissions:
        raise DeleteDirectorMemberResponses.PERMISSION_ERROR
    try:
        deleted_id = await director_service.delete_director_member(director_member_id)
        return deleted_id
    except DirectionBoardMemberNotFoundError:
        raise DeleteDirectorMemberResponses.DIRECTOR_MEMBER_NOT_FOUND


class UploadImageResponses(PermissionsResponses):
    INVALID_CONTENT_TYPE = 415, "Invalid image content type"


@router.post(
    "/images",
    status_code=201,
    responses=UploadImageResponses.responses,
    summary="Upload image for a director member",
)
async def upload_director_member_photo(
    file: Annotated[UploadFile, File(...)],
    admin: AdminUserDep,  # noqa
    permissions: AdminPermissionsDep,
) -> dict:
    if "director_board.update" not in permissions:
        raise UploadImageResponses.PERMISSION_ERROR
    if not file.content_type.startswith("image/"):
        raise UploadImageResponses.INVALID_CONTENT_TYPE

    relative_filepath = await save_file(file, settings.DIRECTORS_BOARD_UPLOADS_PATH)

    return {"path": relative_filepath.as_posix()}


class ReorderCardResponses(PermissionsResponses):
    INVALID_REORDER_ITEMS_COUNT = 409, "Invalid reorder items count"


@router.put(
    "/reorder",
    responses=ReorderCardResponses.responses,
    summary="Reorder directors board members",
)
async def reorder_cards(
    items: list[CardOrderUpdate],
    director_service: DirectorBoardMemberServiceDep,
    admin: AdminUserDep,  # noqa
    permissions: AdminPermissionsDep,
):
    if "director_board.update" not in permissions:
        raise ReorderCardResponses.PERMISSION_ERROR
    try:
        await director_service.update_order(items)
    except InvalidReorderItemsCountError:
        raise ReorderCardResponses.INVALID_REORDER_ITEMS_COUNT
