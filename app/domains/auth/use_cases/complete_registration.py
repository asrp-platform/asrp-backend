from typing import Annotated

from fastapi import Depends

from app.domains.auth.exceptions import EmailConfirmationExpiredError, RegistrationAlreadyCompletedError
from app.domains.auth.services import AuthTokenServiceDep
from app.domains.shared.transaction_managers import TransactionManagerDep


class CompleteRegistrationUseCase:
    def __init__(self, transaction_manager: TransactionManagerDep, token_service: AuthTokenServiceDep):
        self.__tm = transaction_manager
        self.__token_service = token_service

    async def execute(self, token: bytes) -> str:
        try:
            email = self.__token_service.verify_email_confirmation_token(token)
        except ValueError as exc:
            raise EmailConfirmationExpiredError("Invalid or expired token") from exc

        async with self.__tm:
            user = await self.__tm.user_repository.get_by_email(email)
            if user is None:
                raise EmailConfirmationExpiredError("Invalid or expired token")
            if not user.pending:
                raise RegistrationAlreadyCompletedError("User is already registered")

            user.pending = False

        return email


CompleteRegistrationUseCaseDep = Annotated[
    CompleteRegistrationUseCase,
    Depends(CompleteRegistrationUseCase),
]
