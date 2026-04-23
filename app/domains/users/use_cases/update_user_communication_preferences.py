from typing import Annotated

from fastapi import Depends

from app.domains.shared.transaction_managers import TransactionManager, TransactionManagerDep
from app.domains.users.models import CommunicationPreferences
from app.domains.users.services import CommunicationPreferencesService, CommunicationPreferencesServiceDep


class UpdateCommunicationPreferencesUseCase:
    def __init__(
        self,
        transaction_manager: TransactionManager,
        communication_preferences_service: CommunicationPreferencesService,
    ):
        self.__communication_preferences_service = communication_preferences_service
        self.__transaction_manager = transaction_manager

    async def execute(self, user_id: int, current_user_id: int, update_data: dict) -> CommunicationPreferences:
        async with self.__transaction_manager:
            await self.__communication_preferences_service.check_resource_owner(
                user_id,
                current_user_id=current_user_id,
            )
            return await self.__communication_preferences_service.update_or_create_preferences(user_id, update_data)


def get_update_user_communication_preferences_use_case(
    transaction_manager: TransactionManagerDep,
    communication_preferences_service: CommunicationPreferencesServiceDep,
) -> UpdateCommunicationPreferencesUseCase:
    return UpdateCommunicationPreferencesUseCase(transaction_manager, communication_preferences_service)


UpdateCommunicationPreferencesUseCaseDep = Annotated[
    UpdateCommunicationPreferencesUseCase, Depends(get_update_user_communication_preferences_use_case)
]
