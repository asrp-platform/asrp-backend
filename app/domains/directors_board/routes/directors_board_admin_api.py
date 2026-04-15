from typing import Annotated

from fastapi import APIRouter, Depends, File, Path, Response, UploadFile

from app.core.common.responses import PermissionsResponses
from app.domains.directors_board.exceptions import InvalidReorderItemsCountError
from app.domains.directors_board.schemas import (
    BoardMemberSchema,
    CardOrderUpdate,
    CreateBoardMemberSchema,
    UpdateBoardMemberSchema,
)
from app.domains.directors_board.use_cases.create_director_member import CreateDirectorMemberUseCaseDep
from app.domains.directors_board.use_cases.delete_director_member import (
    DeleteDirectorMemberPhotoUseCaseDep,
    DeleteDirectorMemberUseCaseDep,
)
from app.domains.directors_board.use_cases.get_directors_list import GetDirectorsListUseCaseDep
from app.domains.directors_board.use_cases.reorder_directors import ReorderDirectorsUseCaseDep
from app.domains.directors_board.use_cases.update_director_member import (
    UpdateDirectorMemberRequest,
    UpdateDirectorMemberUseCaseDep,
)
from app.domains.directors_board.use_cases.upload_director_member_photo import (
    UploadDirectorMemberPhotoUseCaseDep,
    UploadPhotoRequest,
)
from app.domains.shared.deps import AdminPermissionsDep, get_admin_user

router = APIRouter(prefix="/directors-board", tags=["Admin: Directors board"], dependencies=[Depends(get_admin_user)])


class ViewDirectorResponses(PermissionsResponses):
    pass


@router.get("", responses=ViewDirectorResponses.responses, summary="View all directors board (admin view)")
async def get_all_director_members(
    use_case: GetDirectorsListUseCaseDep,
    permissions: AdminPermissionsDep,
) -> list[BoardMemberSchema]:
    if "director_board.view" not in permissions:
        raise ViewDirectorResponses.PERMISSION_ERROR
    return await use_case.execute()


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
    use_case: CreateDirectorMemberUseCaseDep,
) -> BoardMemberSchema:
    if "director_board.create" not in permissions:
        raise CreateDirectorResponses.PERMISSION_ERROR
    return await use_case.execute(data)


class UpdateDirectorMemberResponses(PermissionsResponses):
    pass


@router.patch(
    "/{director_member_id}",
    responses=UpdateDirectorMemberResponses.responses,
    summary="Update a director board member",
)
async def update_director_member(
    director_member_id: Annotated[int, Path(...)],
    permissions: AdminPermissionsDep,
    use_case: UpdateDirectorMemberUseCaseDep,
    update_data: UpdateBoardMemberSchema,
) -> BoardMemberSchema:
    if "director_board.update" not in permissions:
        raise UpdateDirectorMemberResponses.PERMISSION_ERROR

    return await use_case.execute(UpdateDirectorMemberRequest(director_member_id=director_member_id, data=update_data))


class DeleteDirectorMemberResponses(PermissionsResponses):
    pass


@router.delete(
    "/{director_member_id}",
    responses=DeleteDirectorMemberResponses.responses,
    status_code=204,
    summary="Delete a director board member",
)
async def delete_director_member(
    director_member_id: Annotated[int, Path(...)],
    permissions: AdminPermissionsDep,
    use_case: DeleteDirectorMemberUseCaseDep,
) -> Response:
    if "director_board.delete" not in permissions:
        raise DeleteDirectorMemberResponses.PERMISSION_ERROR

    await use_case.execute(director_member_id)
    return Response(status_code=204)


@router.delete(
    "/{director_member_id}/image",
    status_code=204,
    responses=DeleteDirectorMemberResponses.responses,
    summary="Delete image for a director board member",
)
async def delete_director_member_photo(
    director_member_id: Annotated[int, Path(...)],
    permissions: AdminPermissionsDep,
    use_case: DeleteDirectorMemberPhotoUseCaseDep,
) -> Response:
    if "director_board.update" not in permissions:
        raise DeleteDirectorMemberResponses.PERMISSION_ERROR

    await use_case.execute(director_member_id)
    return Response(status_code=204)


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
    use_case: UploadDirectorMemberPhotoUseCaseDep,
) -> dict:
    if "director_board.update" not in permissions:
        raise UploadImageResponses.PERMISSION_ERROR
    if not file.content_type.startswith("image/"):
        raise UploadImageResponses.INVALID_CONTENT_TYPE

    result = await use_case.execute(UploadPhotoRequest(director_member_id=director_member_id, file=file))

    return {"path": result.path, "presigned_url": result.presigned_url}


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
    use_case: ReorderDirectorsUseCaseDep,
) -> Response:
    if "director_board.update" not in permissions:
        raise ReorderCardResponses.PERMISSION_ERROR
    try:
        await use_case.execute(items)
    except InvalidReorderItemsCountError:
        raise ReorderCardResponses.INVALID_REORDER_ITEMS_COUNT

    return Response(status_code=204)
