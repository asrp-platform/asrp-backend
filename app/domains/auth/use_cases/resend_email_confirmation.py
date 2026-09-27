from typing import Annotated

from fastapi import Depends

from app.core.common.exceptions import NotFoundError
from app.domains.auth.exceptions import EmailAlreadyConfirmedError
from app.domains.auth.services import AuthEmailServiceDep
from app.domains.shared.transaction_managers import TransactionManagerDep


class ResendEmailConfirmationUseCase:
    def __init__(self, transaction_manager: TransactionManagerDep, email_service: AuthEmailServiceDep):
        self.__tm = transaction_manager
        self.__email_service = email_service

    async def execute(self, email: str) -> None:
        async with self.__tm:
            user = await self.__tm.user_repository.get_by_email(email)
            if user is None:
                raise NotFoundError("User with provided email not found")
            if not user.pending:
                raise EmailAlreadyConfirmedError("Provided email is already confirmed")

        await self.__email_service.send_email_confirmation(user)


ResendEmailConfirmationUseCaseDep = Annotated[
    ResendEmailConfirmationUseCase,
    Depends(ResendEmailConfirmationUseCase),
]
