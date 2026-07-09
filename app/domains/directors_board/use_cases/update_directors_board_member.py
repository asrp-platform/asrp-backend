from dataclasses import dataclass
from datetime import datetime
from typing import Annotated

from fastapi import Depends

from app.core.database.base_transaction_manager import BaseTransactionManager
from app.core.utils.permissions import check_permissions
from app.domains.directors_board.services import DirectorBoardMemberServiceDep, DirectorsBoardService
from app.domains.shared.transaction_managers import TransactionManagerDep


@dataclass
class UpdatedDirectorBoardMemberDTO:
    id: int
    created_at: datetime
    updated_at: datetime
    role: str
    name: str
    order: int
    is_visible: bool
    content: dict
    photo_url: str | None = None


class UpdateDirectorsBoardMemberUseCase:
    def __init__(
        self,
        transaction_manager: BaseTransactionManager,
        directors_board_service: DirectorsBoardService,
    ):
        self.__transaction_manager = transaction_manager
        self.__directors_board_service = directors_board_service

    async def execute(self, permissions, director_member_id: int, **kwargs) -> UpdatedDirectorBoardMemberDTO:
        check_permissions("directors_board.update", permissions)
        async with self.__transaction_manager:
            director_member = await self.__directors_board_service.update_director_member(director_member_id, **kwargs)
            photo_url = director_member.photo_url

            if photo_url:
                photo_url = await self.__directors_board_service.get_photo_url_by_object_key(photo_url)

            return UpdatedDirectorBoardMemberDTO(
                id=director_member.id,
                created_at=director_member.created_at,
                updated_at=director_member.updated_at,
                role=director_member.role,
                name=director_member.name,
                photo_url=photo_url,
                order=director_member.order,
                is_visible=director_member.is_visible,
                content=director_member.content,
            )


def get_use_case(
    transaction_manager: TransactionManagerDep,
    directors_board_service: DirectorBoardMemberServiceDep,
) -> UpdateDirectorsBoardMemberUseCase:
    return UpdateDirectorsBoardMemberUseCase(transaction_manager, directors_board_service)


UpdateDirectorsBoardMemberUseCaseDep = Annotated[UpdateDirectorsBoardMemberUseCase, Depends(get_use_case)]
