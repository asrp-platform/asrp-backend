from typing import Annotated

from fastapi import Depends

from app.core.database.base_transaction_manager import BaseTransactionManager
from app.core.utils.permissions import check_permissions
from app.domains.directors_board.services import DirectorBoardMemberServiceDep, DirectorsBoardService
from app.domains.shared.transaction_managers import TransactionManagerDep


class DeleteDirectorsBoardMemberUseCase:
    def __init__(
        self,
        transaction_manager: BaseTransactionManager,
        directors_board_service: DirectorsBoardService,
    ):
        self.__transaction_manager = transaction_manager
        self.__directors_board_service = directors_board_service

    async def execute(self, permissions, director_member_id: int) -> int:
        check_permissions("directors_board.delete", permissions)
        async with self.__transaction_manager:
            return await self.__directors_board_service.delete_director_member(director_member_id)


def get_use_case(
    transaction_manager: TransactionManagerDep,
    directors_board_service: DirectorBoardMemberServiceDep,
) -> DeleteDirectorsBoardMemberUseCase:
    return DeleteDirectorsBoardMemberUseCase(transaction_manager, directors_board_service)


DeleteDirectorsBoardMemberUseCaseDep = Annotated[DeleteDirectorsBoardMemberUseCase, Depends(get_use_case)]
