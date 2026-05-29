from dataclasses import dataclass
from datetime import datetime
from typing import Annotated

from fastapi import Depends

from app.core.database.base_transaction_manager import BaseTransactionManager
from app.domains.directors_board.services import DirectorBoardMemberServiceDep, DirectorsBoardService
from app.domains.shared.transaction_managers import TransactionManagerDep


@dataclass
class DirectorBoardMemberDTO:
        id: int
        created_at: datetime
        updated_at: datetime
        role: str
        name: str
        order: int
        is_visible: bool
        content: dict
        photo_url: str | None = None


class GetDirectorsBoardMembersUseCase:
    def __init__(
        self,
        transaction_manager: BaseTransactionManager,
        directors_board_service: DirectorsBoardService,
    ):
        self.__transaction_manager = transaction_manager
        self.__directors_board_service = directors_board_service

    async def execute(self) -> tuple[list[DirectorBoardMemberDTO], int]:
        # No need to check permissions here
        async with self.__transaction_manager:
            members_orm, count = await self.__directors_board_service.get_directors_board_members()

            members_data = list()
            for member in members_orm:
                member_data = DirectorBoardMemberDTO(
                    id=member.id,
                    created_at=member.created_at,
                    updated_at=member.updated_at,
                    role=member.role,
                    name=member.name,
                    photo_url=member.photo_url,
                    order=member.order,
                    is_visible=member.is_visible,
                    content=member.content,
                )

                if member_data.photo_url:
                    member_data.photo_url = await self.__directors_board_service.get_photo_url_by_object_key(
                        member_data.photo_url
                    )

                members_data.append(member_data)

            return members_data, count

def get_use_case(
    transaction_manager: TransactionManagerDep,
    directors_board_service: DirectorBoardMemberServiceDep,
) -> GetDirectorsBoardMembersUseCase:
    return GetDirectorsBoardMembersUseCase(transaction_manager, directors_board_service)


GetDirectorsBoardMembersUseCaseDep = Annotated[GetDirectorsBoardMembersUseCase, Depends(get_use_case)]
