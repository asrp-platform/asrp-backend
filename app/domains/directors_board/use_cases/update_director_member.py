from dataclasses import dataclass
from typing import Annotated

from fastapi import Depends

from app.core.common.base_use_case import BaseUseCase
from app.domains.directors_board.infrastructure import (
    DirectorsBoardMemberUnitOfWork,
    get_director_board_member_unit_of_work,
)
from app.domains.directors_board.schemas import BoardMemberSchema, UpdateBoardMemberSchema
from app.domains.directors_board.services import DirectorBoardMemberService, get_director_board_member_service


@dataclass
class UpdateDirectorMemberRequest:
    director_member_id: int
    data: UpdateBoardMemberSchema


class UpdateDirectorMemberUseCase(BaseUseCase[UpdateDirectorMemberRequest, BoardMemberSchema]):
    def __init__(self, uow: DirectorsBoardMemberUnitOfWork, service: DirectorBoardMemberService):
        self.uow = uow
        self.service = service

    async def execute(self, request_data: UpdateDirectorMemberRequest) -> BoardMemberSchema:
        async with self.uow:
            member = await self.service.update_director_member(
                request_data.director_member_id,
                request_data.data.model_dump(exclude_unset=True)
            )
            return BoardMemberSchema.model_validate(member)


def get_update_director_member_use_case(
    uow: Annotated[DirectorsBoardMemberUnitOfWork, Depends(get_director_board_member_unit_of_work)],
    service: Annotated[DirectorBoardMemberService, Depends(get_director_board_member_service)],
) -> UpdateDirectorMemberUseCase:
    return UpdateDirectorMemberUseCase(uow, service)


UpdateDirectorMemberUseCaseDep = Annotated[
    UpdateDirectorMemberUseCase, Depends(get_update_director_member_use_case)
]
