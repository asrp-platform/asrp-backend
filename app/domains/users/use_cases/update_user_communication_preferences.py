from typing import Annotated

from fastapi import Depends

from app.core.database.unit_of_work import SQLAlchemyUnitOfWork
from app.domains.users.infrastructure import UserUnitOfWork, get_user_unit_of_work
from app.domains.users.services import CommunicationPreferencesService, get_communication_preferences_service


class UpdateCommunicationPreferencesUseCase:
    def __init__(self, uow: SQLAlchemyUnitOfWork, service: CommunicationPreferencesService):
        self.__service = service
        self.__uow = uow

    async def execute(self, user_id: int, current_user_id: int, update_data: dict):
        async with self.__uow:
            await self.__service.check_resource_owner(user_id, current_user_id=current_user_id)
            return await self.__service.update_or_create_preferences(user_id, update_data)


def get_update_user_communication_preferences_use_case(
    service: Annotated[CommunicationPreferencesService, Depends(get_communication_preferences_service)],
    uow: Annotated[UserUnitOfWork, Depends(get_user_unit_of_work)],
) -> UpdateCommunicationPreferencesUseCase:
    return UpdateCommunicationPreferencesUseCase(uow, service)


UpdateCommunicationPreferencesUseCaseDep = Annotated[
    UpdateCommunicationPreferencesUseCase, Depends(get_update_user_communication_preferences_use_case)
]
