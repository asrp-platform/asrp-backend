from typing import Annotated

from fastapi import Depends

from app.core.database.unit_of_work import SQLAlchemyUnitOfWork
from app.domains.users.infrastructure import UserUnitOfWork, get_user_unit_of_work
from app.domains.users.services import CommunicationPreferencesService, get_communication_preferences_service


class RetrieveCommunicationPreferencesUseCase:
    def __init__(self, uow: SQLAlchemyUnitOfWork, service: CommunicationPreferencesService):
        self._service = service
        self._uow = uow

    async def execute(self, user_id: int):
        async with self._uow:
            return await self._service.get_or_create(user_id)


def get_retrieve_user_communication_preferences_use_case(
    service: Annotated[CommunicationPreferencesService, Depends(get_communication_preferences_service)],
    uow: Annotated[UserUnitOfWork, Depends(get_user_unit_of_work)],
) -> RetrieveCommunicationPreferencesUseCase:
    return RetrieveCommunicationPreferencesUseCase(uow, service)


RetrieveCommunicationPreferencesUseCaseDep = Annotated[
    RetrieveCommunicationPreferencesUseCase, Depends(get_retrieve_user_communication_preferences_use_case)
]
