from typing import Annotated

from fastapi import Depends

from app.core.common.base_use_case import BaseUseCase
from app.domains.directors_board.infrastructure import (
    DirectorsBoardMemberUnitOfWork,
    get_director_board_member_unit_of_work,
)
from app.domains.directors_board.schemas import CardOrderUpdate
from app.domains.directors_board.services import DirectorBoardMemberService, get_director_board_member_service


class ReorderDirectorsUseCase(BaseUseCase[list[CardOrderUpdate], None]):
    def __init__(self, uow: DirectorsBoardMemberUnitOfWork, service: DirectorBoardMemberService):
        self.uow = uow
        self.service = service

    async def execute(self, request_data: list[CardOrderUpdate]) -> None:
        async with self.uow:
            await self.service.reorder_cards(request_data)


def get_reorder_directors_use_case(
    uow: Annotated[DirectorsBoardMemberUnitOfWork, Depends(get_director_board_member_unit_of_work)],
    service: Annotated[DirectorBoardMemberService, Depends(get_director_board_member_service)],
) -> ReorderDirectorsUseCase:
    return ReorderDirectorsUseCase(uow, service)


ReorderDirectorsUseCaseDep = Annotated[
    ReorderDirectorsUseCase, Depends(get_reorder_directors_use_case)
]
