from typing import Annotated

from fastapi import Depends
from sqlalchemy import func, select

from app.domains.directors_board.infrastructure import (
    DirectorBoardMemberUnitOfWork,
    get_director_board_member_unit_of_work,
)
from app.domains.directors_board.models import DirectorBoardMember


class DirectorBoardMemberService:
    def __init__(self, uow):
        self.uow: DirectorBoardMemberUnitOfWork = uow

    async def get_all_directors(self):
        async with self.uow:
            return await self.uow.director_board_member_repository.list()

    async def create_director(self, **kwargs):
        max_order = (
            await self.uow._session.execute(select(func.coalesce(func.max(DirectorBoardMember.order), 0)))
        ).scalar_one_or_none()
        insert_data = {**kwargs, "order": max_order + 1}
        async with self.uow:
            return await self.uow.director_board_member_repository.create(**insert_data)


def get_director_board_member_service(
    uow: Annotated[DirectorBoardMemberUnitOfWork, Depends(get_director_board_member_unit_of_work)],
) -> DirectorBoardMemberService:
    return DirectorBoardMemberService(uow)


DirectorBoardMemberServiceDep = Annotated[DirectorBoardMemberService, Depends(get_director_board_member_service)]
