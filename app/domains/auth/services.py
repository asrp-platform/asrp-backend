from datetime import datetime, timezone
from typing import Annotated

from fastapi import Depends
from fastapi_exception_responses import Responses

from app.core.common.cryptographer import Cryptographer
from app.core.config import fernet, settings
from app.domains.auth.exceptions import (
    EmailAlreadyConfirmedError,
    EmailConfirmationExpiredError,
    RegistrationAlreadyCompletedError,
)
from app.domains.auth.schemas import RegisterFormData
from app.domains.emails.plugins.gmail_plugin import GmailPlugin
from app.domains.emails.services import get_email_service
from app.domains.shared.transaction_managers import TransactionManager, TransactionManagerDep
from app.domains.users.exceptions import UserNotFoundError


class RegisterResponses(Responses):
    EMAIL_ALREADY_IN_USE = 409, "Provided email is already in use"


class AuthService:
    def __init__(self, transaction_manager: TransactionManager):
        self.transaction_manager = transaction_manager
        self.cryptographer = Cryptographer(fernet)
        self.email_provider = get_email_service(GmailPlugin)

    async def register_user(self, register_form_data: RegisterFormData):
        """Creates or extends subscription"""

        user_data = register_form_data.model_dump()
        user_data.pop("repeat_password")

        email = user_data["email"]

        async with self.transaction_manager:
            existing_user = await self.transaction_manager.user_repository.get_first_by_kwargs(email=email)

            if existing_user is None:
                user = await self.transaction_manager.user_repository.create(**user_data, pending=True)

            elif existing_user.pending is True:
                existing_user.firstname = user_data["firstname"]
                existing_user.lastname = user_data["lastname"]
                existing_user.country = user_data["country"]
                existing_user.city = user_data["city"]
                existing_user.password = user_data["password"]
                existing_user.pending = True

                user = existing_user

            else:
                raise RegisterResponses.EMAIL_ALREADY_IN_USE

        await self.send_email_confirm_link(email)
        return user

    async def set_new_password(self, email, password):
        async with self.transaction_manager:
            user = await self.transaction_manager.user_repository.get_first_by_kwargs(email=email)

            if user is None:
                raise UserNotFoundError("User with provided email not found")

            user.password = password
            await self.transaction_manager._session.flush()  # noqa property's setter manual calling
            await self.transaction_manager.user_repository.update(
                user.id, last_password_change=datetime.now(tz=timezone.utc)
            )

    async def reset_password(self, email: str):
        async with self.transaction_manager:
            user = await self.transaction_manager.user_repository.get_first_by_kwargs(email=email)

        if user is None:
            return

        token = self.cryptographer.create_token(email)
        link = f"{settings.FRONTEND_DOMAIN}/password-reset/confirm/?token={token.decode()}"
        message = f"""
        Hello,

        We received a request to reset the password for your account ({email}).
        Please click the link below to set a new password:

        {link}

        This link is valid for 1 hour. If you did not request a password reset, please ignore this message.

        """
        await self.email_provider.send_email(to=email, subject="Password Reset", body=message)

    async def send_email_confirm_link(self, email: str):
        token = self.cryptographer.create_token(email)
        link = f"{settings.FRONTEND_DOMAIN}/registration/complete?token={token.decode()}"
        message = f"""
        Hello,

        Thank you for registering! To complete your registration and confirm your email address, please follow the link below:

        {link}

        This link is valid for 1 day. If you did not create an account, please ignore this message.
        """
        await self.email_provider.send_email(to=email, subject="Email Confirmation", body=message)

    async def resend_email_confirmation_link(self, email: str):
        async with self.transaction_manager:
            existing_user = await self.transaction_manager.user_repository.get_first_by_kwargs(email=email)

            if existing_user is None:
                raise UserNotFoundError("User with provided email not found")

            if existing_user.pending is False:
                raise EmailAlreadyConfirmedError("Provided email is already confirmed")

        await self.send_email_confirm_link(email)

    async def complete_registration(self, token: bytes) -> str:
        try:
            email = self.verify_email_confirmation_token(token)

        except ValueError as e:
            raise EmailConfirmationExpiredError("Invalid or expired token") from e

        async with self.transaction_manager:
            user = await self.transaction_manager.user_repository.get_first_by_kwargs(email=email)

            if user is None:
                raise EmailConfirmationExpiredError("Invalid or expired token")

            if user.pending is False:
                raise RegistrationAlreadyCompletedError("User is already registered")

            user.pending = False

        return email

    def verify_password_reset_token(self, token: bytes) -> str:
        lifetime_seconds = 3600  # 1 hour
        return self.cryptographer.verify_token(token, lifetime_seconds)

    def verify_email_confirmation_token(self, token: bytes) -> str:
        lifetime_seconds = 86400  # 1 day
        return self.cryptographer.verify_token(token, lifetime_seconds)


def get_auth_service(transaction_manager: TransactionManagerDep) -> AuthService:
    return AuthService(transaction_manager)


AuthServiceDep = Annotated[AuthService, Depends(get_auth_service)]
