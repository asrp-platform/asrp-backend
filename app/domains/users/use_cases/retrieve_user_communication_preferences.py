from dataclasses import dataclass
from typing import Annotated

from fastapi import Depends

from app.core.common.base_use_case import BaseUseCase
from app.core.database.base_transaction_manager import SQLAlchemyTransactionManagerBase
from app.domains.users.infrastructure import UserTransactionManagerBase, get_user_unit_of_work
from app.domains.users.models import CommunicationPreferences
from app.domains.users.services import CommunicationPreferencesService, get_communication_preferences_service


@dataclass
class RetrieveCommunicationPreferencesRequest:
    user_id: int


class RetrieveCommunicationPreferencesUseCase(
    BaseUseCase[RetrieveCommunicationPreferencesRequest, CommunicationPreferences]
):
    def __init__(self, uow: SQLAlchemyTransactionManagerBase, service: CommunicationPreferencesService):
        self.__service = service
        self.__uow = uow

    async def execute(self, request: RetrieveCommunicationPreferencesRequest) -> CommunicationPreferences:
        async with self.__uow:
            return await self.__service.get_or_create(request.user_id)


def get_retrieve_user_communication_preferences_use_case(
    service: Annotated[CommunicationPreferencesService, Depends(get_communication_preferences_service)],
    uow: Annotated[UserTransactionManagerBase, Depends(get_user_unit_of_work)],
) -> RetrieveCommunicationPreferencesUseCase:
    return RetrieveCommunicationPreferencesUseCase(uow, service)


RetrieveCommunicationPreferencesUseCaseDep = Annotated[
    RetrieveCommunicationPreferencesUseCase, Depends(get_retrieve_user_communication_preferences_use_case)
]
