from typing import Annotated

from fastapi import Depends

from app.core.common.exceptions import InvalidMimeTypeError
from app.core.config import s3_storage
from app.core.utils.permissions import check_permissions
from app.domains.shared.types import FileData


class UploadDirectorsBoardMemberPhotoUseCase:
    def __init__(self):
        self.__file_storage = s3_storage

    async def execute(self, permissions, file_data: FileData) -> str:
        """Returns presigned URL for uploaded image."""
        check_permissions("directors_board.update", permissions)

        if not file_data.content_type.startswith("image/"):
            raise InvalidMimeTypeError("Invalid image content type")

        uploaded_file_data = await self.__file_storage.upload_file(
            f"directors_board/{file_data.filename}", file=file_data.content
        )

        return await self.__file_storage.get_presigned_object(uploaded_file_data.object_key)


def get_use_case() -> UploadDirectorsBoardMemberPhotoUseCase:
    return UploadDirectorsBoardMemberPhotoUseCase()


UploadDirectorsBoardMemberPhotoUseCaseDep = Annotated[UploadDirectorsBoardMemberPhotoUseCase, Depends(get_use_case)]
