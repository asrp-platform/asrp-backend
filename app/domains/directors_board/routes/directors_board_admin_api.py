from typing import Annotated

from fastapi import APIRouter, Depends, File, Path, Response, UploadFile

from app.core.common.responses import PermissionsResponses
from app.domains.directors_board.exceptions import DirectionBoardMemberNotFoundError, InvalidReorderItemsCountError
from app.domains.directors_board.schemas import (
    BoardMemberSchema,
    CardOrderUpdate,
    CreateBoardMemberSchema,
    UpdateBoardMemberSchema,
)
from app.domains.directors_board.services import DirectorBoardMemberServiceDep
from app.domains.shared.deps import AdminPermissionsDep, get_admin_user

router = APIRouter(prefix="/directors-board", tags=["Admin: Directors board"], dependencies=[Depends(get_admin_user)])


class ViewDirectorResponses(PermissionsResponses):
    pass


@router.get("", responses=ViewDirectorResponses.responses, summary="View all directors board (admin view)")
async def get_all_director_members(
    director_service: DirectorBoardMemberServiceDep,
    permissions: AdminPermissionsDep,
) -> list[BoardMemberSchema]:
    if "director_board.view" not in permissions:
        raise ViewDirectorResponses.PERMISSION_ERROR
    data, count = await director_service.get_all_directors()
    return data


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
    permissions: AdminPermissionsDep,
    director_service: DirectorBoardMemberServiceDep,
) -> BoardMemberSchema:
    if "director_board.create" not in permissions:
        raise CreateDirectorResponses.PERMISSION_ERROR
    return await director_service.create_director_member(**data.model_dump())


class UpdateDirectorMemberResponses(PermissionsResponses):
    DIRECTOR_MEMBER_NOT_FOUND = 404, "Director member with provided ID not found"


@router.patch(
    "/{director_member_id}",
    responses=UpdateDirectorMemberResponses.responses,
    summary="Update a director board member",
)
async def update_director_member(
    director_member_id: Annotated[int, Path(...)],
    permissions: AdminPermissionsDep,
    director_service: DirectorBoardMemberServiceDep,
    update_data: UpdateBoardMemberSchema,
) -> BoardMemberSchema:
    if "director_board.update" not in permissions:
        raise UpdateDirectorMemberResponses.PERMISSION_ERROR
    
    update_data_dict = update_data.model_dump(exclude_unset=True)
    return await director_service.update_director_member(director_member_id, update_data_dict)


class DeleteDirectorMemberResponses(PermissionsResponses):
    DIRECTOR_MEMBER_NOT_FOUND = 404, "Director member with provided ID not found"


@router.delete(
    "/{director_member_id}",
    responses=DeleteDirectorMemberResponses.responses,
    summary="Delete a director board member",
)
async def delete_director_member(
    director_member_id: Annotated[int, Path(...)],
    permissions: AdminPermissionsDep,
    director_service: DirectorBoardMemberServiceDep,
) -> int:
    if "director_board.delete" not in permissions:
        raise DeleteDirectorMemberResponses.PERMISSION_ERROR

    return await director_service.delete_director_member(director_member_id)


@router.delete(
    "/{director_member_id}/image",
    status_code=204,
    responses=DeleteDirectorMemberResponses.responses,
    summary="Delete image for a director board member",
)
async def delete_director_member_photo(
    director_member_id: Annotated[int, Path(...)],
    permissions: AdminPermissionsDep,
    director_service: DirectorBoardMemberServiceDep,
) -> None:
    if "director_board.update" not in permissions:
        raise DeleteDirectorMemberResponses.PERMISSION_ERROR
    
    await director_service.delete_photo(director_member_id)


class UploadImageResponses(PermissionsResponses):
    INVALID_CONTENT_TYPE = 415, "Invalid image content type"


@router.post(
    "/{director_member_id}/image",
    status_code=201,
    responses=UploadImageResponses.responses,
    summary="Upload image for a director member",
)
async def upload_director_member_photo(
    director_member_id: Annotated[int, Path(...)],
    file: Annotated[UploadFile, File(...)],
    permissions: AdminPermissionsDep,
    director_service: DirectorBoardMemberServiceDep,
) -> dict:
    if "director_board.update" not in permissions:
        raise UploadImageResponses.PERMISSION_ERROR
    if not file.content_type.startswith("image/"):
        raise UploadImageResponses.INVALID_CONTENT_TYPE

    filename = await director_service.upload_photo(director_member_id, file)

    return {"path": filename}


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
    permissions: AdminPermissionsDep,
):
    if "director_board.update" not in permissions:
        raise ReorderCardResponses.PERMISSION_ERROR
    try:
        await director_service.update_order(items)
    except InvalidReorderItemsCountError:
        raise ReorderCardResponses.INVALID_REORDER_ITEMS_COUNT
