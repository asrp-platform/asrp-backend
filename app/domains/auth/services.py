from datetime import datetime, timezone
from typing import Annotated

from fastapi import Depends
from fastapi_exception_responses import Responses

from app.core.common.cryptographer import Cryptographer
from app.core.config import fernet, settings
from app.domains.auth.infrastructure import AuthUnitOfWork, get_auth_unit_of_work
from app.domains.auth.schemas import RegisterFormData
from app.domains.emails.plugins.gmail_plugin import GmailPlugin
from app.domains.emails.services import get_email_service


class RegisterResponses(Responses):
    PASSWORDS_DONT_MATCH = 400, "Passwords don't match"
    EMAIL_ALREADY_IN_USE = 409, "Provided email is already in use"
    EMAIL_ALREADY_CONFIRMED = 409, "Provided email is already confirmed"


class AuthService:
    def __init__(self, uow):
        self.uow: AuthUnitOfWork = uow
        self.cryptographer = Cryptographer(fernet)
        self.email_provider = get_email_service(GmailPlugin)

    async def register_user(self, register_form_data: RegisterFormData):
        """Creates or extends subscription"""

        user_data = register_form_data.model_dump()

        if (await self.uow.user_repository.get_first_by_kwargs(email=user_data["email"])) is not None:
            raise RegisterResponses.EMAIL_ALREADY_IN_USE

        if user_data["password"] != user_data.pop("repeat_password"):
            raise RegisterResponses.PASSWORDS_DONT_MATCH

        async with self.uow:
            user = await self.uow.user_repository.create(**user_data)

        return user

    async def change_password(self, email, password):
        async with self.uow:
            user = await self.uow.user_repository.get_first_by_kwargs(email=email)

            if user is None:
                raise ValueError("user with provided email not found")

            user.password = password
            await self.uow._session.flush()  # noqa property's setter manual calling
            await self.uow.user_repository.update(user.id, {"last_password_change": datetime.now(tz=timezone.utc)})

    async def reset_password(self, email: str):
        async with self.uow:

            user = await self.uow.user_repository.get_first_by_kwargs(email=email)

        if user is None:
            return

        token = self.cryptographer.create_token(email)
        link = f"{settings.FRONTEND_DOMAIN}/auth/password-reset/confirm/?token={token.decode()}"
        message = f"""
        Hello,

        We received a request to reset the password for your account ({email}).
        Please click the link below to set a new password:

        {link}

        This link is valid for 1 hour. If you did not request a password reset, please ignore this message.

        """
        await self.email_provider.send_email(to=email, subject="Password Reset", body=message)

    async def send_email_confirm_link(self, email: str, email_confirmed: bool):
        if email_confirmed:
            raise ValueError("Provided email is already confirmed")

        token = self.cryptographer.create_token(email)
        link = f"{settings.FRONTEND_DOMAIN}/auth/email-confirm/confirm/?token={token.decode()}"
        message = f"""
        Hello,

        Thank you for registering! To complete your account setup and verify your email address, please click the link below:

        {link}

        This link is valid for 1 day. If you did not request a password reset, please ignore this message.
        """
        await self.email_provider.send_email(to=email, subject="Email Confirmation", body=message)

    async def confirm_email(self, current_user_id: int, token_email: str, current_user_email: str):
        async with self.uow:

            if current_user_email != token_email:
                raise ValueError("email of the confirmation token does not match email of the authorized user")

            await self.uow.user_repository.update(current_user_id, {"email_confirmed": True})

    def verify_password_reset_token(self, token: bytes) -> str:
        lifetime_seconds = 3600  # 1 hour
        return self.cryptographer.verify_token(token, lifetime_seconds)

    def verify_email_confirm_token(self, token: bytes) -> str:
        lifetime_seconds = 86400  # 1 day
        return self.cryptographer.verify_token(token, lifetime_seconds)


def get_auth_service(uow: Annotated[AuthUnitOfWork, Depends(get_auth_unit_of_work)]) -> AuthService:
    return AuthService(uow)


AuthServiceDep = Annotated[AuthService, Depends(get_auth_service)]
