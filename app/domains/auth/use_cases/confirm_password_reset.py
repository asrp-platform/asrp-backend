from datetime import datetime, timezone
from typing import Annotated

from fastapi import Depends

from app.core.common.exceptions import NotFoundError
from app.domains.auth.services import AuthTokenServiceDep
from app.domains.shared.transaction_managers import TransactionManagerDep


class ConfirmPasswordResetUseCase:
    def __init__(self, transaction_manager: TransactionManagerDep, token_service: AuthTokenServiceDep):
        self.__tm = transaction_manager
        self.__token_service = token_service

    async def execute(self, token: bytes, password: str) -> None:
        email = self.__token_service.verify_password_reset_token(token)

        async with self.__tm:
            user = await self.__tm.user_repository.get_by_email(email)
            if user is None:
                raise NotFoundError("User with provided email not found")

            user.password = password
            await self.__tm._session.flush()  # noqa: property's setter manually changes the hash
            await self.__tm.user_repository.update(user.id, last_password_change=datetime.now(tz=timezone.utc))


ConfirmPasswordResetUseCaseDep = Annotated[ConfirmPasswordResetUseCase, Depends(ConfirmPasswordResetUseCase)]
