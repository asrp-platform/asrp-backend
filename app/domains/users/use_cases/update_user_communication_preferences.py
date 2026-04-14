from dataclasses import dataclass
from typing import Annotated

from fastapi import Depends

from app.core.common.base_use_case import BaseUseCase
from app.core.database.base_transaction_manager import SQLAlchemyTransactionManagerBase
from app.domains.users.infrastructure import UserTransactionManagerBase, get_user_unit_of_work
from app.domains.users.models import CommunicationPreferences
from app.domains.users.services import CommunicationPreferencesService, get_communication_preferences_service


@dataclass
class UpdateCommunicationPreferencesRequest:
    user_id: int
    current_user_id: int
    update_data: dict


class UpdateCommunicationPreferencesUseCase(
    BaseUseCase[UpdateCommunicationPreferencesRequest, CommunicationPreferences]
):
    def __init__(self, uow: SQLAlchemyTransactionManagerBase, service: CommunicationPreferencesService):
        self.__service = service
        self.__uow = uow

    async def execute(self, request: UpdateCommunicationPreferencesRequest) -> CommunicationPreferences:
        async with self.__uow:
            await self.__service.check_resource_owner(request.user_id, current_user_id=request.current_user_id)
            return await self.__service.update_or_create_preferences(request.user_id, request.update_data)


def get_update_user_communication_preferences_use_case(
    service: Annotated[CommunicationPreferencesService, Depends(get_communication_preferences_service)],
    uow: Annotated[UserTransactionManagerBase, Depends(get_user_unit_of_work)],
) -> UpdateCommunicationPreferencesUseCase:
    return UpdateCommunicationPreferencesUseCase(uow, service)


UpdateCommunicationPreferencesUseCaseDep = Annotated[
    UpdateCommunicationPreferencesUseCase, Depends(get_update_user_communication_preferences_use_case)
]
