from typing import Annotated

from fastapi import APIRouter, Depends, File, Path, UploadFile

from app.core.common.exceptions import PermissionDeniedError
from app.core.common.responses import PermissionsResponses
from app.domains.directors_board.exceptions import DirectionBoardMemberNotFoundError, InvalidReorderItemsCountError
from app.domains.directors_board.schemas import (
    BoardMemberSchema,
    CardOrderUpdate,
    CreateBoardMemberSchema,
    UpdateBoardMemberSchema,
)
from app.domains.directors_board.use_cases.create_directors_board_member import CreateDirectorsBoardMemberUseCaseDep
from app.domains.directors_board.use_cases.delete_directors_board_member import DeleteDirectorsBoardMemberUseCaseDep
from app.domains.directors_board.use_cases.get_directors_board_members import GetDirectorsBoardMembersUseCaseDep
from app.domains.directors_board.use_cases.reorder_directors_board_members import ReorderDirectorsBoardMembersUseCaseDep
from app.domains.directors_board.use_cases.update_directors_board_member import UpdateDirectorsBoardMemberUseCaseDep
from app.domains.directors_board.use_cases.upload_directors_board_member_photo import (
    UploadDirectorsBoardMemberPhotoUseCaseDep,
)
from app.domains.shared.deps import AdminPermissionsDep, get_admin_user

router = APIRouter(prefix="/directors-board", tags=["Admin: Directors board"], dependencies=[Depends(get_admin_user)])


@router.get("", summary="View all directors board (admin view)")
async def get_all_director_members(
    use_case: GetDirectorsBoardMembersUseCaseDep,
) -> list[BoardMemberSchema]:
    data, count = await use_case.execute()
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
    use_case: CreateDirectorsBoardMemberUseCaseDep,
) -> BoardMemberSchema:
    return await use_case.execute(permissions, **data.model_dump())


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
    use_case: UpdateDirectorsBoardMemberUseCaseDep,
    update_data: UpdateBoardMemberSchema,
) -> BoardMemberSchema:
    try:
        update_data_dict = update_data.model_dump(exclude_unset=True)
        updated_director_member = await use_case.execute(permissions, director_member_id, update_data_dict)
        return updated_director_member

    except PermissionDeniedError:
        raise UpdateDirectorMemberResponses.PERMISSION_ERROR
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
    permissions: AdminPermissionsDep,
    use_case: DeleteDirectorsBoardMemberUseCaseDep,
) -> int:
    try:
        deleted_id = await use_case.execute(permissions, director_member_id)
        return deleted_id
    except PermissionDeniedError:
        raise DeleteDirectorMemberResponses.PERMISSION_ERROR
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
    permissions: AdminPermissionsDep,
    use_case: UploadDirectorsBoardMemberPhotoUseCaseDep,
) -> dict:
    try:
        return await use_case.execute(permissions, file)
    except PermissionDeniedError:
        raise UploadImageResponses.PERMISSION_ERROR
    except ValueError:
        raise UploadImageResponses.INVALID_CONTENT_TYPE


class ReorderCardResponses(PermissionsResponses):
    INVALID_REORDER_ITEMS_COUNT = 409, "Invalid reorder items count"


@router.put(
    "/reorder",
    responses=ReorderCardResponses.responses,
    summary="Reorder directors board members",
)
async def reorder_cards(
    items: list[CardOrderUpdate],
    permissions: AdminPermissionsDep,
    use_case: ReorderDirectorsBoardMembersUseCaseDep,
):
    try:
        await use_case.execute(permissions, items)
    except PermissionDeniedError:
        raise ReorderCardResponses.PERMISSION_ERROR
    except InvalidReorderItemsCountError:
        raise ReorderCardResponses.INVALID_REORDER_ITEMS_COUNT
