from typing import Annotated

from fastapi import Depends

from app.core.common.base_use_case import BaseUseCase
from app.domains.directors_board.infrastructure import (
    DirectorsBoardMemberUnitOfWork,
    get_director_board_member_unit_of_work,
)
from app.domains.directors_board.schemas import BoardMemberSchema, CreateBoardMemberSchema
from app.domains.directors_board.services import DirectorBoardMemberService, get_director_board_member_service


class CreateDirectorMemberUseCase(BaseUseCase[CreateBoardMemberSchema, BoardMemberSchema]):
    def __init__(self, uow: DirectorsBoardMemberUnitOfWork, service: DirectorBoardMemberService):
        self.uow = uow
        self.service = service

    async def execute(self, request_data: CreateBoardMemberSchema) -> BoardMemberSchema:
        async with self.uow:
            member = await self.service.create_director_member(**request_data.model_dump())
            return BoardMemberSchema.model_validate(member)


def get_create_director_member_use_case(
    uow: Annotated[DirectorsBoardMemberUnitOfWork, Depends(get_director_board_member_unit_of_work)],
    service: Annotated[DirectorBoardMemberService, Depends(get_director_board_member_service)],
) -> CreateDirectorMemberUseCase:
    return CreateDirectorMemberUseCase(uow, service)


CreateDirectorMemberUseCaseDep = Annotated[
    CreateDirectorMemberUseCase, Depends(get_create_director_member_use_case)
]
