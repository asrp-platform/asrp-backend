from typing import Annotated

from fastapi import Depends

from app.domains.shared.transaction_managers import TransactionManager, TransactionManagerDep
from app.domains.users.models import CommunicationPreferences
from app.domains.users.services import CommunicationPreferencesService, CommunicationPreferencesServiceDep


class RetrieveCommunicationPreferencesUseCase:
    def __init__(self, transaction_manager: TransactionManager, service: CommunicationPreferencesService):
        self.__service = service
        self.__transaction_manager = transaction_manager

    async def execute(self, user_id: int) -> CommunicationPreferences:
        async with self.__transaction_manager:
            return await self.__service.get_or_create(user_id)


def get_retrieve_user_communication_preferences_use_case(
    transaction_manager: TransactionManagerDep,
    service: CommunicationPreferencesServiceDep,
) -> RetrieveCommunicationPreferencesUseCase:
    return RetrieveCommunicationPreferencesUseCase(transaction_manager, service)


RetrieveCommunicationPreferencesUseCaseDep = Annotated[
    RetrieveCommunicationPreferencesUseCase, Depends(get_retrieve_user_communication_preferences_use_case)
]
