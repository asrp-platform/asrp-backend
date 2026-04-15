from typing import Annotated

from fastapi import Depends

from app.core.common.base_use_case import BaseUseCase
from app.domains.directors_board.infrastructure import DirectorsBoardMemberUnitOfWork, get_director_board_member_unit_of_work
from app.domains.directors_board.schemas import BoardMemberSchema
from app.domains.directors_board.services import DirectorBoardMemberService, get_director_board_member_service


class GetDirectorsListUseCase(BaseUseCase[None, list[BoardMemberSchema]]):
    def __init__(self, uow: DirectorsBoardMemberUnitOfWork, service: DirectorBoardMemberService):
        self.uow = uow
        self.service = service

    async def execute(self, request_data: None = None) -> list[BoardMemberSchema]:
        async with self.uow:
            members, count = await self.service.get_all_directors()
            
            result = []
            for member in members:
                schema = BoardMemberSchema.model_validate(member)
                schema.photo_url = await self.service.get_photo_url(member.photo_url)
                result.append(schema)
                
            return result


def get_directors_list_use_case(
    uow: Annotated[DirectorsBoardMemberUnitOfWork, Depends(get_director_board_member_unit_of_work)],
    service: Annotated[DirectorBoardMemberService, Depends(get_director_board_member_service)],
) -> GetDirectorsListUseCase:
    return GetDirectorsListUseCase(uow, service)


GetDirectorsListUseCaseDep = Annotated[GetDirectorsListUseCase, Depends(get_directors_list_use_case)]
