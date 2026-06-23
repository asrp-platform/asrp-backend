from typing import Annotated

from fastapi import Depends

from app.domains.shared.transaction_managers import TransactionManagerDep
from app.domains.users.models import CommunicationPreferences
from app.domains.users.services import CommunicationPreferencesServiceDep


class RetrieveCommunicationPreferencesUseCase:
    def __init__(self, transaction_manager: TransactionManagerDep, service: CommunicationPreferencesServiceDep):
        self.__service = service
        self.__tm = transaction_manager

    async def execute(self, user_id: int) -> CommunicationPreferences:
        async with self.__tm:
            return await self.__service.get_communication_preferences(user_id)


RetrieveCommunicationPreferencesUseCaseDep = Annotated[
    RetrieveCommunicationPreferencesUseCase, Depends(RetrieveCommunicationPreferencesUseCase)
]
