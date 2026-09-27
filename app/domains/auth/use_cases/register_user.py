from typing import Annotated

from fastapi import Depends

from app.core.common.exceptions import ResourceAlreadyExistsError
from app.domains.auth.schemas import RegisterFormData
from app.domains.auth.services import AuthEmailServiceDep
from app.domains.shared.transaction_managers import TransactionManagerDep
from app.domains.users.models import User


class RegisterUserUseCase:
    """Register a new user or refresh an existing pending registration."""

    def __init__(self, transaction_manager: TransactionManagerDep, email_service: AuthEmailServiceDep):
        self.__tm = transaction_manager
        self.__email_service = email_service

    async def execute(self, register_form_data: RegisterFormData) -> User:
        user_data = register_form_data.model_dump()
        user_data.pop("repeat_password")
        email = user_data["email"]

        async with self.__tm:
            existing_user: User = await self.__tm.user_repository.get_by_email(email)

            if existing_user is None:
                user = await self.__tm.user_repository.create(**user_data, pending=True)
                await self.__tm.flush()
                await self.__tm.communication_preferences_repository.create(user_id=user.id)
            elif existing_user.pending:
                for field in (
                    "firstname",
                    "lastname",
                    "country",
                    "city",
                    "state",
                    "postal_code",
                    "password",
                    "credentials",
                ):
                    setattr(existing_user, field, user_data[field])
                user = existing_user
            else:
                raise ResourceAlreadyExistsError("Provided email is already in use")

        await self.__email_service.send_email_confirmation(user)

        return user


RegisterUserUseCaseDep = Annotated[RegisterUserUseCase, Depends(RegisterUserUseCase)]
