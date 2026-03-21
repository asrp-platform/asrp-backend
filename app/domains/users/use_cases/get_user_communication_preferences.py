from typing import Annotated

from fastapi import Depends

from app.domains.users.services import CommunicationPreferencesService, get_communication_preferences_service


class RetrieveCommunicationPreferencesUseCase:
    def __init__(self, service: CommunicationPreferencesService):
        self._service = service

    async def execute(self, user_id: int):
        return await self._service.get_or_create(user_id)


def get_retrieve_user_communication_preferences_use_case(
    service: Annotated[CommunicationPreferencesService, Depends(get_communication_preferences_service)],
) -> RetrieveCommunicationPreferencesUseCase:
    return RetrieveCommunicationPreferencesUseCase(service)


RetrieveCommunicationPreferencesUseCaseDep = Annotated[
    RetrieveCommunicationPreferencesUseCase, Depends(get_retrieve_user_communication_preferences_use_case)
]
