from datetime import datetime, timedelta, timezone
from typing import Annotated

from fastapi import Depends
from jose import jwt

from app.core.common.cryptographer import Cryptographer
from app.core.config import fernet, settings
from app.domains.auth.exceptions import InvalidPasswordResetTokenError
from app.domains.emails.common.messages import MessageBuilder
from app.domains.emails.email_queue import EmailQueue
from app.domains.users.models import User


class AuthTokenService:
    def __init__(self):
        self.__cryptographer = Cryptographer(fernet)

    def create_password_reset_token(self, email: str) -> bytes:
        return self.__cryptographer.create_token(email)

    def verify_password_reset_token(self, token: bytes) -> str:
        try:
            return self.__cryptographer.verify_token(token, 3600)
        except ValueError:
            raise InvalidPasswordResetTokenError("Invalid token")

    def create_email_confirmation_token(self, email: str) -> bytes:
        return self.__cryptographer.create_token(email)

    def verify_email_confirmation_token(self, token: bytes) -> str:
        return self.__cryptographer.verify_token(token, 86400)


class AuthJwtService:
    def __init__(self):
        self.__settings = settings

    def create_access_token(self, data: dict) -> str:
        expire = datetime.now(timezone.utc) + timedelta(minutes=self.__settings.ACCESS_TOKEN_LIFESPAN_MINUTES)
        return jwt.encode(
            {**data, "exp": expire},
            self.__settings.SECRET_KEY,
            algorithm=self.__settings.ALGORITHM,
        )

    def create_refresh_token(self, data: dict, remember_me: bool = False) -> str:
        lifetime = (
            timedelta(days=self.__settings.REFRESH_TOKEN_REMEMBER_ME_LIFETIME_DAYS)
            if remember_me
            else timedelta(days=self.__settings.REFRESH_TOKEN_LIFETIME_DAYS)
        )
        expire = datetime.now(timezone.utc) + lifetime
        return jwt.encode(
            {**data, "exp": expire},
            self.__settings.SECRET_KEY,
            algorithm=self.__settings.ALGORITHM,
        )


class AuthEmailService:
    def __init__(self, token_service: Annotated[AuthTokenService, Depends()]):
        self.__token_service = token_service

    async def send_password_reset(self, email: str):
        token = self.__token_service.create_password_reset_token(email)
        link = f"{settings.FRONTEND_DOMAIN}/password-reset/confirm/?token={token.decode()}"
        subject, body = MessageBuilder.build_password_reset_html(reset_link=link)

        EmailQueue.send_email(
            to=email,
            subject=subject,
            body=body,
        )

    async def send_email_confirmation(self, user: User):
        token = self.__token_service.create_email_confirmation_token(user.email)
        link = f"{settings.FRONTEND_DOMAIN}/registration/complete?token={token.decode()}"

        subject, body = MessageBuilder.build_email_verification_html(full_name=user.full_name, verification_link=link)
        EmailQueue.send_email(to=user.email, subject=subject, body=body)


AuthTokenServiceDep = Annotated[AuthTokenService, Depends(AuthTokenService)]
AuthEmailServiceDep = Annotated[AuthEmailService, Depends(AuthEmailService)]
AuthJwtServiceDep = Annotated[AuthJwtService, Depends(AuthJwtService)]
