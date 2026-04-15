from typing import Annotated

from fastapi import Depends

from app.core.common.base_use_case import BaseUseCase
from app.domains.directors_board.infrastructure import (
    DirectorsBoardMemberUnitOfWork,
    get_director_board_member_unit_of_work,
)
from app.domains.directors_board.services import DirectorBoardMemberService, get_director_board_member_service


class DeleteDirectorMemberUseCase(BaseUseCase[int, int]):
    def __init__(self, uow: DirectorsBoardMemberUnitOfWork, service: DirectorBoardMemberService):
        self.uow = uow
        self.service = service

    async def execute(self, director_member_id: int) -> int:
        async with self.uow:
            return await self.service.delete_director_member(director_member_id)


def get_delete_director_member_use_case(
    uow: Annotated[DirectorsBoardMemberUnitOfWork, Depends(get_director_board_member_unit_of_work)],
    service: Annotated[DirectorBoardMemberService, Depends(get_director_board_member_service)],
) -> DeleteDirectorMemberUseCase:
    return DeleteDirectorMemberUseCase(uow, service)


DeleteDirectorMemberUseCaseDep = Annotated[
    DeleteDirectorMemberUseCase, Depends(get_delete_director_member_use_case)
]


class DeleteDirectorMemberPhotoUseCase(BaseUseCase[int, None]):
    def __init__(self, uow: DirectorsBoardMemberUnitOfWork, service: DirectorBoardMemberService):
        self.uow = uow
        self.service = service

    async def execute(self, director_member_id: int) -> None:
        async with self.uow:
            await self.service.delete_photo(director_member_id)


def get_delete_director_member_photo_use_case(
    uow: Annotated[DirectorsBoardMemberUnitOfWork, Depends(get_director_board_member_unit_of_work)],
    service: Annotated[DirectorBoardMemberService, Depends(get_director_board_member_service)],
) -> DeleteDirectorMemberPhotoUseCase:
    return DeleteDirectorMemberPhotoUseCase(uow, service)


DeleteDirectorMemberPhotoUseCaseDep = Annotated[
    DeleteDirectorMemberPhotoUseCase, Depends(get_delete_director_member_photo_use_case)
]
