from typing import Annotated

from fastapi import Depends, UploadFile

from app.core.config import settings
from app.core.utils.permissions import check_permissions
from app.core.utils.save_file import save_file


class UploadDirectorsBoardMemberPhotoUseCase:
    async def execute(self, permissions, file: UploadFile) -> dict:
        check_permissions("directors_board.update", permissions)

        if not file.content_type.startswith("image/"):
            raise ValueError("Invalid image content type")

        relative_filepath = await save_file(file, settings.DIRECTORS_BOARD_UPLOADS_PATH)
        return {"path": relative_filepath.as_posix()}


def get_use_case() -> UploadDirectorsBoardMemberPhotoUseCase:
    return UploadDirectorsBoardMemberPhotoUseCase()


UploadDirectorsBoardMemberPhotoUseCaseDep = Annotated[UploadDirectorsBoardMemberPhotoUseCase, Depends(get_use_case)]
