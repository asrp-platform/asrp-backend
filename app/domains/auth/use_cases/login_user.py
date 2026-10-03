from dataclasses import dataclass
from typing import Annotated

from fastapi import Depends

from app.core.config import settings
from app.domains.auth.exceptions import InvalidCredentialsError, UserBannedError
from app.domains.auth.schemas import LoginForm
from app.domains.auth.services import AuthJwtServiceDep
from app.domains.shared.transaction_managers import TransactionManagerDep


@dataclass(frozen=True)
class LoginResult:
    access_token: str
    refresh_token: str
    refresh_token_max_age: int


class LoginUserUseCase:
    def __init__(self, transaction_manager: TransactionManagerDep, jwt_service: AuthJwtServiceDep):
        self.__tm = transaction_manager
        self.__jwt_service = jwt_service

    async def execute(self, login_data: LoginForm) -> LoginResult:
        async with self.__tm:
            user = await self.__tm.user_repository.get_by_email(login_data.email)

            if user is None or user.pending or not user.verify_password(login_data.password):
                raise InvalidCredentialsError("Wrong credentials")

            if user.banned:
                raise UserBannedError(f"User is banned: {user.ban_reason}")

        token_data = {"email": user.email}
        refresh_token = self.__jwt_service.create_refresh_token(token_data, remember_me=login_data.remember)
        return LoginResult(
            access_token=self.__jwt_service.create_access_token(token_data),
            refresh_token=refresh_token,
            refresh_token_max_age=(
                settings.refresh_token_cookie_max_age_seconds_remember
                if login_data.remember
                else settings.refresh_token_cookie_max_age_seconds
            ),
        )


LoginUserUseCaseDep = Annotated[LoginUserUseCase, Depends(LoginUserUseCase)]
