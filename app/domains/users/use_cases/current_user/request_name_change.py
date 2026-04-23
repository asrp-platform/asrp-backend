from typing import Annotated

from fastapi import Depends

from app.domains.shared.transaction_managers import TransactionManager, TransactionManagerDep
from app.domains.users.models import User
from app.domains.users.services import NameChangeRequestService, NameChangeRequestServiceDep


class RequestNageChangeUseCase:
    def __init__(
        self,
        transaction_manager: TransactionManager,
        name_change_request_service: NameChangeRequestService,
    ):
        self.__transaction_manager = transaction_manager
        self.__name_change_request_service = name_change_request_service

    async def execute(self, current_user: User, **kwargs):
        """Only for current authenticated user"""
        async with self.__transaction_manager:
            return await self.__name_change_request_service.create_name_change_request(current_user.id, **kwargs)


def get_use_case(
    transaction_manager: TransactionManagerDep,
    name_change_request_service: NameChangeRequestServiceDep,
) -> RequestNageChangeUseCase:
    return RequestNageChangeUseCase(transaction_manager, name_change_request_service)


RequestNageChangeUseCaseDep = Annotated[RequestNageChangeUseCase, Depends(get_use_case)]
