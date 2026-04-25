from typing import Annotated

from fastapi import Depends

from app.core.database.base_transaction_manager import BaseTransactionManager
from app.core.utils.permissions import check_permissions
from app.domains.directors_board.schemas import CardOrderUpdate
from app.domains.directors_board.services import DirectorBoardMemberServiceDep, DirectorsBoardService
from app.domains.shared.transaction_managers import TransactionManagerDep


class ReorderDirectorsBoardMembersUseCase:
    def __init__(
        self,
        transaction_manager: BaseTransactionManager,
        directors_board_service: DirectorsBoardService,
    ):
        self.__transaction_manager = transaction_manager
        self.__directors_board_service = directors_board_service

    async def execute(self, permissions, items: list[CardOrderUpdate]) -> None:
        check_permissions("directors_board.update", permissions)
        async with self.__transaction_manager:
            await self.__directors_board_service.update_order(items)


def get_use_case(
    transaction_manager: TransactionManagerDep,
    directors_board_service: DirectorBoardMemberServiceDep,
) -> ReorderDirectorsBoardMembersUseCase:
    return ReorderDirectorsBoardMembersUseCase(transaction_manager, directors_board_service)


ReorderDirectorsBoardMembersUseCaseDep = Annotated[ReorderDirectorsBoardMembersUseCase, Depends(get_use_case)]
