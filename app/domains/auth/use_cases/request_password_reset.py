from typing import Annotated

from fastapi import Depends

from app.domains.auth.services import AuthEmailServiceDep
from app.domains.shared.transaction_managers import TransactionManagerDep


class RequestPasswordResetUseCase:
    def __init__(self, transaction_manager: TransactionManagerDep, email_service: AuthEmailServiceDep):
        self.__tm = transaction_manager
        self.__email_service = email_service

    async def execute(self, email: str) -> None:
        async with self.__tm:
            user = await self.__tm.user_repository.get_by_email(email)

        if user is not None:
            await self.__email_service.send_password_reset(email)


RequestPasswordResetUseCaseDep = Annotated[RequestPasswordResetUseCase, Depends(RequestPasswordResetUseCase)]
