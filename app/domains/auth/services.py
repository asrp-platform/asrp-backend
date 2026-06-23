from datetime import datetime, timezone
from typing import Annotated

from fastapi import Depends
from fastapi_exception_responses import Responses

from app.core.common.cryptographer import Cryptographer
from app.core.common.exceptions import NotFoundError
from app.core.config import fernet, settings
from app.domains.auth.exceptions import (
    EmailAlreadyConfirmedError,
    EmailConfirmationExpiredError,
    RegistrationAlreadyCompletedError,
)
from app.domains.auth.schemas import RegisterFormData
from app.domains.emails.common.messages import build_email_verification_html, build_password_reset_html
from app.domains.emails.email_queue import EmailQueueDep
from app.domains.shared.transaction_managers import TransactionManagerDep
from app.domains.users.models import User


class RegisterResponses(Responses):
    EMAIL_ALREADY_IN_USE = 409, "Provided email is already in use"


class AuthService:
    def __init__(self, transaction_manager: TransactionManagerDep, email_queue: EmailQueueDep):
        self.__tm = transaction_manager
        self.cryptographer = Cryptographer(fernet)
        self.__email_queue = email_queue

    async def register_user(self, register_form_data: RegisterFormData):
        user_data = register_form_data.model_dump()
        user_data.pop("repeat_password")
        email = user_data["email"]

        async with self.__tm:
            existing_user: User = await self.__tm.user_repository.get_first_by_kwargs(email=email)

            if existing_user is None:
                user = await self.__tm.user_repository.create(**user_data, pending=True)
                await self.__tm.communication_preferences_repository.create()

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

        token = self.cryptographer.create_token(user.email)
        link = f"{settings.FRONTEND_DOMAIN}/registration/complete?token={token.decode()}"

        subject, body = build_email_verification_html(full_name=user.full_name, verification_link=link)
        await self.__email_queue.send_email(to=user.email, subject=subject, body=body)

        return user

    async def set_new_password(self, email, password):
        async with self.__tm:
            user = await self.__tm.user_repository.get_first_by_kwargs(email=email)

            if user is None:
                raise NotFoundError("User with provided email not found")

            user.password = password
            await self.__tm._session.flush()  # noqa property's setter manual calling
            await self.__tm.user_repository.update(user.id, last_password_change=datetime.now(tz=timezone.utc))

    async def reset_password(self, email: str):
        async with self.__tm:
            user = await self.__tm.user_repository.get_first_by_kwargs(email=email)

        if user is None:
            return

        token = self.cryptographer.create_token(email)
        link = f"{settings.FRONTEND_DOMAIN}/password-reset/confirm/?token={token.decode()}"
        subject, body = build_password_reset_html(reset_link=link)

        await self.__email_queue.send_email(
            to=email,
            subject=subject,
            body=body,
        )

    async def send_email_confirm_link(self, user: User):
        token = self.cryptographer.create_token(user.email)
        link = f"{settings.FRONTEND_DOMAIN}/registration/complete?token={token.decode()}"

        subject, body = build_email_verification_html(full_name=user.full_name, verification_link=link)
        await self.__email_queue.send_email(to=user.email, subject=subject, body=body)

    async def resend_email_confirmation_link(self, email: str):
        async with self.__tm:
            existing_user = await self.__tm.user_repository.get_first_by_kwargs(email=email)

            if existing_user is None:
                raise NotFoundError("User with provided email not found")

            if existing_user.pending is False:
                raise EmailAlreadyConfirmedError("Provided email is already confirmed")

        await self.send_email_confirm_link(existing_user)

    async def complete_registration(self, token: bytes) -> str:
        try:
            email = self.verify_email_confirmation_token(token)

        except ValueError as e:
            raise EmailConfirmationExpiredError("Invalid or expired token") from e

        async with self.__tm:
            user = await self.__tm.user_repository.get_first_by_kwargs(email=email)

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


AuthServiceDep = Annotated[AuthService, Depends(AuthService)]
