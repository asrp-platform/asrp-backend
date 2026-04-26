from typing import Annotated

from fastapi import Depends

from app.core.database.base_transaction_manager import BaseTransactionManager
from app.domains.directors_board.models import DirectorBoardMember
from app.domains.directors_board.services import DirectorBoardMemberServiceDep, DirectorsBoardService
from app.domains.shared.transaction_managers import TransactionManagerDep


class GetDirectorsBoardMembersUseCase:
    def __init__(
        self,
        transaction_manager: BaseTransactionManager,
        directors_board_service: DirectorsBoardService,
    ):
        self.__transaction_manager = transaction_manager
        self.__directors_board_service = directors_board_service

    async def execute(self) -> DirectorBoardMember:
        # No need to check permissions here
        async with self.__transaction_manager:
            return await self.__directors_board_service.get_directors_board_members()


def get_use_case(
    transaction_manager: TransactionManagerDep,
    directors_board_service: DirectorBoardMemberServiceDep,
) -> GetDirectorsBoardMembersUseCase:
    return GetDirectorsBoardMembersUseCase(transaction_manager, directors_board_service)


GetDirectorsBoardMembersUseCaseDep = Annotated[GetDirectorsBoardMembersUseCase, Depends(get_use_case)]
