from dataclasses import dataclass
from typing import Annotated

from fastapi import Depends, UploadFile

from app.core.common.base_use_case import BaseUseCase
from app.domains.directors_board.infrastructure import DirectorsBoardMemberUnitOfWork, get_director_board_member_unit_of_work
from app.domains.directors_board.services import DirectorBoardMemberService, get_director_board_member_service


@dataclass
class UploadPhotoRequest:
    director_member_id: int
    file: UploadFile


@dataclass
class UploadPhotoResponse:
    path: str
    presigned_url: str | None


class UploadDirectorMemberPhotoUseCase(BaseUseCase[UploadPhotoRequest, UploadPhotoResponse]):
    def __init__(self, uow: DirectorsBoardMemberUnitOfWork, service: DirectorBoardMemberService):
        self.uow = uow
        self.service = service

    async def execute(self, request_data: UploadPhotoRequest) -> UploadPhotoResponse:
        # Сервис сам управляет транзакцией внутри upload_photo
        filename = await self.service.upload_photo(request_data.director_member_id, request_data.file)
        
        url = await self.service.get_photo_url(filename)
        
        return UploadPhotoResponse(path=filename, presigned_url=url)


def get_upload_director_member_photo_use_case(
    uow: Annotated[DirectorsBoardMemberUnitOfWork, Depends(get_director_board_member_unit_of_work)],
    service: Annotated[DirectorBoardMemberService, Depends(get_director_board_member_service)],
) -> UploadDirectorMemberPhotoUseCase:
    return UploadDirectorMemberPhotoUseCase(uow, service)


UploadDirectorMemberPhotoUseCaseDep = Annotated[
    UploadDirectorMemberPhotoUseCase, Depends(get_upload_director_member_photo_use_case)
]
