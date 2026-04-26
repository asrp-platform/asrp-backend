from typing import Annotated

from fastapi import APIRouter, Depends, File, Path, UploadFile

from app.core.common.exceptions import InvalidMimeTypeError
from app.core.common.responses import PermissionsResponses
from app.domains.directors_board.exceptions import InvalidReorderItemsCountError
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
from app.domains.shared.schemas import UploadedImageSchema
from app.domains.shared.types import FileData

router = APIRouter(prefix="/directors-board", tags=["Admin: Directors board"], dependencies=[Depends(get_admin_user)])


@router.get("", summary="View all directors board (admin view)")
async def get_all_directors_board_members(
    use_case: GetDirectorsBoardMembersUseCaseDep,
) -> list[BoardMemberSchema]:
    data, count = await use_case.execute()
    return data


class CreateDirectorsBoardMemberResponses(PermissionsResponses):
    pass


@router.post(
    "",
    status_code=201,
    responses=CreateDirectorsBoardMemberResponses.responses,
    summary="Create a director board member",
)
async def create_directors_board_member(
    data: CreateBoardMemberSchema,
    permissions: AdminPermissionsDep,
    use_case: CreateDirectorsBoardMemberUseCaseDep,
) -> BoardMemberSchema:
    return await use_case.execute(permissions, **data.model_dump())


class UpdateDirectorsBoardMemberResponses(PermissionsResponses):
    DIRECTOR_MEMBER_NOT_FOUND = 404, "Director member with provided ID not found"


@router.patch(
    "/{director_member_id}",
    responses=UpdateDirectorsBoardMemberResponses.responses,
    summary="Update a director board member",
)
async def update_directors_board_member(
    director_member_id: Annotated[int, Path(...)],
    permissions: AdminPermissionsDep,
    use_case: UpdateDirectorsBoardMemberUseCaseDep,
    update_data: UpdateBoardMemberSchema,
) -> BoardMemberSchema:
    return await use_case.execute(permissions, director_member_id, **update_data.model_dump(exclude_unset=True))


class DeleteDirectorsBoardMemberResponses(UpdateDirectorsBoardMemberResponses):
    pass


@router.delete(
    "/{director_member_id}",
    responses=DeleteDirectorsBoardMemberResponses.responses,
    summary="Delete a director board member",
)
async def delete_directors_board_member(
    director_member_id: Annotated[int, Path(...)],
    permissions: AdminPermissionsDep,
    use_case: DeleteDirectorsBoardMemberUseCaseDep,
) -> int:
    return await use_case.execute(permissions, director_member_id)


class UploadImageResponses(PermissionsResponses):
    INVALID_CONTENT_TYPE = 415, "Invalid image content type"


@router.put(
    "/images",
    responses=UploadImageResponses.responses,
    summary="Upload image for a director member",
)
async def upload_directors_board_member_photo(
    file: Annotated[UploadFile, File(...)],
    permissions: AdminPermissionsDep,
    use_case: UploadDirectorsBoardMemberPhotoUseCaseDep,
) -> UploadedImageSchema:
    file_data = FileData(
        content=await file.read(),
        content_type=file.content_type,
        filename=file.filename,
    )

    try:
        file_path = await use_case.execute(permissions, file_data)
        return UploadedImageSchema(path=file_path)
    except InvalidMimeTypeError:
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
    except InvalidReorderItemsCountError:
        raise ReorderCardResponses.INVALID_REORDER_ITEMS_COUNT
