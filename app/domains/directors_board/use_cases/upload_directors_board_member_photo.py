from typing import Annotated

from fastapi import Depends

from app.core.utils.permissions import check_permissions
from app.domains.directors_board.services import DirectorBoardMemberServiceDep, DirectorsBoardService
from app.domains.shared.types import FileData


class UploadDirectorsBoardMemberPhotoUseCase:
    def __init__(
            self,
            directors_board_service: DirectorsBoardService,
    ):
        self.__directors_board_service = directors_board_service

    async def execute(self, permissions, director_member_id: int, file_data: FileData) -> str:
        """Returns presigned URL for uploaded image."""
        check_permissions("directors_board.update", permissions)

        object_key = await self.__directors_board_service.upload_photo(director_member_id, file_data)
        return await self.__directors_board_service.get_photo_url_by_object_key(object_key)


def get_use_case(directors_board_service: DirectorBoardMemberServiceDep) -> UploadDirectorsBoardMemberPhotoUseCase:
    return UploadDirectorsBoardMemberPhotoUseCase(directors_board_service)


UploadDirectorsBoardMemberPhotoUseCaseDep = Annotated[UploadDirectorsBoardMemberPhotoUseCase, Depends(get_use_case)]
