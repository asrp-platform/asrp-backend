from typing import Annotated

from fastapi import Depends
from sqlalchemy import func, select, update

from app.domains.directors_board.infrastructure import (
    DirectorsBoardMemberUnitOfWork,
    get_director_board_member_unit_of_work,
)
from app.domains.directors_board.models import DirectorBoardMember


class DirectorBoardMemberService:
    def __init__(self, uow):
        self.uow: DirectorsBoardMemberUnitOfWork = uow

    async def get_all_directors(self):
        async with self.uow:
            return await self.uow.director_board_member_repository.list()

    async def create_director_member(self, **kwargs):
        max_order = (
            await self.uow._session.execute(select(func.coalesce(func.max(DirectorBoardMember.order), 0)))
        ).scalar_one_or_none()
        insert_data = {**kwargs, "order": max_order + 1}
        async with self.uow:
            return await self.uow.director_board_member_repository.create(**insert_data)

    async def update_director_member(self, director_member_id: int, data: dict):
        async with self.uow:
            return await self.uow.director_board_member_repository.update(director_member_id, **data)

    async def delete_director_member(self, director_member_id: int) -> int:
        async with self.uow:
            return await self.uow.director_board_member_repository.mark_as_deleted(director_member_id)

    async def update_order(self, items):
        async with self.uow:
            # Temporary order for second card to exclude order duplication
            await self.uow._session.execute(
                update(DirectorBoardMember).where(DirectorBoardMember.id == items[1].id).values(order=9999)
            )

            for item in items:
                await self.uow._session.execute(
                    update(DirectorBoardMember).where(DirectorBoardMember.id == item.id).values(order=item.order)
                )
                await self.uow._session.commit()


def get_director_board_member_service(
    uow: Annotated[DirectorsBoardMemberUnitOfWork, Depends(get_director_board_member_unit_of_work)],
) -> DirectorBoardMemberService:
    return DirectorBoardMemberService(uow)


DirectorBoardMemberServiceDep = Annotated[DirectorBoardMemberService, Depends(get_director_board_member_service)]
