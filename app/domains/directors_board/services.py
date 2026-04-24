from typing import Annotated

from fastapi import Depends
from sqlalchemy import func, select, update

from app.domains.directors_board.models import DirectorBoardMember
from app.domains.shared.transaction_managers import TransactionManagerDep


class DirectorsBoardService:
    def __init__(self, transaction_manager):
        self.transaction_manager = transaction_manager

    async def get_directors_board_members(self):
        async with self.transaction_manager:
            return await self.transaction_manager.directors_board_member_repository.list()

    async def create_director_member(self, **kwargs):
        max_order = (
            await self.transaction_manager._session.execute(
                select(func.coalesce(func.max(DirectorBoardMember.order), 0))
            )
        ).scalar_one_or_none()
        insert_data = {**kwargs, "order": max_order + 1}
        return await self.transaction_manager.directors_board_member_repository.create(**insert_data)

    async def update_director_member(self, director_member_id: int, data: dict):
        async with self.transaction_manager:
            return await self.transaction_manager.directors_board_member_repository.update(director_member_id, **data)

    async def delete_director_member(self, director_member_id: int) -> int:
        async with self.transaction_manager:
            return await self.transaction_manager.directors_board_member_repository.mark_as_deleted(director_member_id)

    async def update_order(self, items):
        async with self.transaction_manager:
            # Temporary order for second card to exclude order duplication
            await self.transaction_manager._session.execute(
                update(DirectorBoardMember).where(DirectorBoardMember.id == items[1].id).values(order=9999)
            )

            for item in items:
                await self.transaction_manager._session.execute(
                    update(DirectorBoardMember).where(DirectorBoardMember.id == item.id).values(order=item.order)
                )
                await self.transaction_manager._session.commit()


def get_director_board_member_service(transaction_manager: TransactionManagerDep) -> DirectorsBoardService:
    return DirectorsBoardService(transaction_manager)


DirectorBoardMemberServiceDep = Annotated[DirectorsBoardService, Depends(get_director_board_member_service)]
