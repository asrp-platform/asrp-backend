import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Annotated, Any

from fastapi import Depends
from loguru import logger

from app.core.common.exceptions import NotResourceOwnerError
from app.core.config import BASE_DIR, settings
from app.domains.users.exceptions import (
    FellowshipNotFoundError,
    InvalidPasswordError,
    ResidencyNotFoundError,
    UserNotFoundError,
    UsernameChangeNotFoundError,
    ActiveUsernameChangeAlreadyExistsError,
    UsernameChangeCooldownNotExpiredError
)
from app.domains.users.infrastructure import UserUnitOfWork, get_user_unit_of_work
from app.domains.users.models import (
    Fellowship,
    ProfessionalInformation,
    Residency,
    User,
    UsernameChange,
    UsernameChangeStatusEnum
)

"""
Не использую HTTPExceptions в сервисах, так как
это сделало бы сервисы зависимыми от фреймворка
"""


class UserService:
    def __init__(self, uow):
        self.uow = uow

    async def get_all_paginated_counted(
        self, limit: int = None, offset: int = None, order_by: str = None, filters: dict[str, Any] = None
    ) -> [list[User], int]:
        async with self.uow:
            return await self.uow.user_repository.list(limit, offset, order_by, filters)

    async def get_all_users_count(self) -> int:
        async with self.uow:
            return await self.uow.user_repository.get_count()

    async def create(self, **kwargs):
        async with self.uow:
            return await self.uow.user_repository.create(**kwargs)

    async def get_user_by_kwargs(self, **kwargs) -> User:
        async with self.uow:
            return await self.uow.user_repository.get_first_by_kwargs(**kwargs)

    async def set_user_avatar(self, user_id: int, avatar_path: Path):
        async with self.uow:
            user = await self.uow.user_repository.get_first_by_kwargs(id=user_id)
            if user is None:
                raise UserNotFoundError("User with provided ID not found")
            try:
                os.remove(BASE_DIR / user.avatar_path)
            except FileNotFoundError as e:
                logger.error(f"Avatar deletion error\nTarget path: {BASE_DIR / user.avatar_path}\n Error: {e}")

            except Exception as e:
                logger.error(f"Unexpected error: {e}")

            await self.uow.user_repository.update(user_id, {"avatar_path": avatar_path})

    async def update_user(self, user_id: int, update_data: dict) -> User:
        async with self.uow:
            user = await self.uow.user_repository.get_first_by_kwargs(id=user_id)
            if user is None:
                raise UserNotFoundError("User with provided ID not found")
            await self.uow.user_repository.update(user_id, update_data)
        return user

    async def delete_avatar(self, user_id: int) -> None:
        async with self.uow:
            user = await self.uow.user_repository.get_first_by_kwargs(id=user_id)
            if user is None:
                raise UserNotFoundError("User with provided ID not found")
            try:
                os.remove(BASE_DIR / user.avatar_path)
            except FileNotFoundError as e:
                logger.error(f"Avatar deletion error\nTarget path: {BASE_DIR / user.avatar_path}\n Error: {e}")

            except Exception as e:
                logger.error(f"Unexpected error: {e}")

            await self.uow.user_repository.update(user_id, {"avatar_path": None})

    async def change_password(self, user_id, old_password, new_password):
        async with self.uow:
            user = await self.uow.user_repository.get_first_by_kwargs(id=user_id)

            if user is None:
                raise UserNotFoundError("user with provided email not found")

            if not user.verify_password(old_password):
                raise InvalidPasswordError("Invalid password")

            user.password = new_password
            await self.uow._session.flush()  # noqa property's setter manual calling
            await self.uow.user_repository.update(user.id, {"last_password_change": datetime.now(tz=timezone.utc)})


class ProfessionalInformationService:
    def __init__(self, uow):
        self.uow = uow

    async def get_by_user_id(self, user_id: int) -> ProfessionalInformation | None:
        async with self.uow:
            user = await self.uow.user_repository.get_first_by_kwargs(id=user_id)
            if user is None:
                raise UserNotFoundError("User with provided ID not found")
            return await self.uow.professional_information_repository.get_first_by_kwargs(user_id=user_id)

    async def create_or_update(self, user_id: int, current_user_id: int, **kwargs) -> ProfessionalInformation:
        if user_id != current_user_id:
            raise NotResourceOwnerError("Not resource owner")

        async with self.uow:
            user = await self.uow.user_repository.get_first_by_kwargs(id=user_id)

            if user is None:
                raise UserNotFoundError("User with provided ID not found")

            professional_information = await self.uow.professional_information_repository.get_first_by_kwargs(
                user_id=user_id
            )
            data = {**kwargs, "user_id": user.id}

            if professional_information is not None:
                return await self.uow.professional_information_repository.update(professional_information.id, data)
            else:
                return await self.uow.professional_information_repository.create(**data)


class ResidencyService:
    def __init__(self, uow):
        self.uow = uow

    async def check_resource_owner(self, user_id: int, *, current_user_id: int = None, residency_id: int = None):
        """
        Ensures:
        - user exists
        - residency exists (optional)
        - current user is a resource owner (optional)
        """
        async with self.uow:
            user = await self.uow.user_repository.get_first_by_kwargs(id=user_id)

            if user is None:
                raise UserNotFoundError("User with provided ID not found")

            if current_user_id is not None and user_id != current_user_id:
                raise NotResourceOwnerError("Not resource owner")

            if residency_id is not None:
                residency = await self.uow.residency_repository.get_first_by_kwargs(id=residency_id, user_id=user_id)

                if residency is None:
                    raise ResidencyNotFoundError("Residency with provided ID not found")

    async def get_by_user_id(self, user_id: int) -> list[Residency]:
        await self.check_resource_owner(user_id)
        async with self.uow:
            return await self.uow.residency_repository.get_all_by_kwargs(user_id=user_id)

    async def get_user_residency_by_id(self, user_id: int, residency_id: int) -> Residency:
        await self.check_resource_owner(user_id, residency_id=residency_id)
        async with self.uow:
            residency = await self.uow.residency_repository.get_first_by_kwargs(id=residency_id, user_id=user_id)
            return residency

    async def create_user_residency(self, user_id: int, current_user_id: int, **kwargs) -> Residency:
        await self.check_resource_owner(user_id, current_user_id=current_user_id)
        async with self.uow:
            return await self.uow.residency_repository.create(user_id=user_id, **kwargs)

    async def update_user_residency(
        self,
        user_id: int,
        current_user_id: int,
        residency_id: int,
        update_data: dict,
    ) -> Residency:
        await self.check_resource_owner(user_id, current_user_id=current_user_id, residency_id=residency_id)
        async with self.uow:
            return await self.uow.residency_repository.update(residency_id, update_data)

    async def delete_user_residency(self, user_id: int, current_user_id: int, residency_id: int) -> int:
        await self.check_resource_owner(user_id, current_user_id=current_user_id, residency_id=residency_id)
        async with self.uow:
            return await self.uow.residency_repository.mark_as_deleted(residency_id)


class FellowshipService:
    def __init__(self, uow):
        self.uow = uow

    async def check_resource_owner(
        self,
        user_id: int,
        *,
        current_user_id: int = None,
        fellowship_id: int = None,
    ):
        """
        Ensures:
        - user exists
        - fellowship exists (optional)
        - current user is a resource owner (optional)
        """
        async with self.uow:
            user = await self.uow.user_repository.get_first_by_kwargs(id=user_id)

            if user is None:
                raise UserNotFoundError("User with provided ID not found")

            if current_user_id is not None and user_id != current_user_id:
                raise NotResourceOwnerError("Not resource owner")

            if fellowship_id is not None:
                fellowship = await self.uow.fellowship_repository.get_first_by_kwargs(
                    id=fellowship_id,
                    user_id=user_id,
                )

                if fellowship is None:
                    raise FellowshipNotFoundError("Fellowship with provided ID not found")

    async def get_by_user_id(self, user_id: int) -> list[Fellowship]:
        await self.check_resource_owner(user_id)
        async with self.uow:
            return await self.uow.fellowship_repository.get_all_by_kwargs(user_id=user_id)

    async def get_user_fellowship_by_id(
        self,
        user_id: int,
        fellowship_id: int,
    ) -> Fellowship:
        await self.check_resource_owner(
            user_id,
            fellowship_id=fellowship_id,
        )
        async with self.uow:
            return await self.uow.fellowship_repository.get_first_by_kwargs(
                id=fellowship_id,
                user_id=user_id,
            )

    async def create_user_fellowship(
        self,
        user_id: int,
        current_user_id: int,
        **kwargs,
    ) -> Fellowship:
        await self.check_resource_owner(
            user_id,
            current_user_id=current_user_id,
        )
        async with self.uow:
            return await self.uow.fellowship_repository.create(
                user_id=user_id,
                **kwargs,
            )

    async def update_user_fellowship(
        self,
        user_id: int,
        current_user_id: int,
        fellowship_id: int,
        update_data: dict,
    ) -> Fellowship:
        await self.check_resource_owner(
            user_id,
            current_user_id=current_user_id,
            fellowship_id=fellowship_id,
        )
        async with self.uow:
            return await self.uow.fellowship_repository.update(
                fellowship_id,
                update_data,
            )

    async def delete_user_fellowship(
        self,
        user_id: int,
        current_user_id: int,
        fellowship_id: int,
    ) -> int:
        await self.check_resource_owner(
            user_id,
            current_user_id=current_user_id,
            fellowship_id=fellowship_id,
        )
        async with self.uow:
            return await self.uow.fellowship_repository.mark_as_deleted(fellowship_id)


class UsernameChangeService:
    def __init__(self, uow: UserUnitOfWork):
        self.uow = uow


    async def check_existence_resource(
            self,
            user_id: int,
            *,
            current_user_id: int | None = None,
            username_change_id: int | None = None,
    ) -> None:
        async with self.uow:
            user = await self.uow.user_repository.get_first_by_kwargs(id=user_id)

            if user is None:
                raise UserNotFoundError("User with provided ID not found")

            if current_user_id is not None and user_id != current_user_id:
                raise NotResourceOwnerError("Not resource owner")

            if username_change_id is not None:
                username_change = await self.uow.username_change_repository.get_first_by_kwargs(
                    id=username_change_id,
                    user_id=user_id
                )
                if username_change is None:
                    raise UsernameChangeNotFoundError("Username change request with provided ID not found")


    async def get_active_username_change(
        self,
        user_id: int,
        username_change_id: int
    ) -> UsernameChange:
        await self.check_existence_resource(user_id, username_change_id=username_change_id)

        async with self.uow:
            return await self.uow.username_change_repository.get_first_by_kwargs(
                id=username_change_id,
                status=UsernameChangeStatusEnum.ACTIVE
            )


    async def get_all_active_username_changes(self) -> list[UsernameChange]:
        async with self.uow:
            username_changes, _ = await self.uow.username_change_repository.list(
                filters={"status": UsernameChangeStatusEnum.ACTIVE},
            )
            return username_changes


    async def get_last_username_change_by_user_id(self, user_id: int) -> UsernameChange | None:
        async with self.uow:
            username_change, _ = await self.uow.username_change_repository.list(
                filters={"user_id": user_id},
                limit=1,
                order_by="-created_at",
            )

            if username_change:
                return username_change[0]
            return None


    async def create_username_change(self, user_id: int, **kwargs) -> UsernameChange:
        await self.check_existence_resource(user_id)

        async with self.uow:
            user = await self.uow.user_repository.get_first_by_kwargs(id=user_id)
            username_change = await self.get_last_username_change_by_user_id(user_id=user_id)

            if username_change is not None and username_change.status == UsernameChangeStatusEnum.ACTIVE:
                raise ActiveUsernameChangeAlreadyExistsError(
                    "Active username change request for User with provided ID is already exists"
                )

            cooldown = settings.USERNAME_CHANGE_COOLDOWN_DAYS
            if username_change is not None and cooldown is not None and user.last_name_change is not None:
                days_elapsed = (datetime.now(tz=timezone.utc) - user.last_name_change).days

                if days_elapsed < cooldown:
                    raise UsernameChangeCooldownNotExpiredError(
                        "The time until the next username change request for User with provided ID has not passed yet"
                    )

            return await self.uow.username_change_repository.create(user_id=user_id, **kwargs)


    async def approve_username_change(
        self,
        user_id: int,
        username_change_id: int
    ) -> None:
        await self.check_existence_resource(user_id, username_change_id=username_change_id)

        async with self.uow:
            username_change = await self.uow.username_change_repository.get_first_by_kwargs(id=username_change_id)

            await self.uow.user_repository.update(
                user_id,
                {
                    "firstname": username_change.firstname,
                    "lastname": username_change.lastname,
                    "last_name_change": datetime.now(tz=timezone.utc)
                }
            )

            await self.uow.username_change_repository.update(
                username_change_id,
                {"status": UsernameChangeStatusEnum.APPROVED}
            )


    async def reject_username_change(
        self,
        user_id: int,
        username_change_id: int,
        reject_username_change_data: dict
    ) -> None:
        await self.check_existence_resource(user_id, username_change_id=username_change_id)

        async with self.uow:
            await self.uow.username_change_repository.update(
                username_change_id,
                reject_username_change_data
            )


def get_user_service(uow: Annotated[UserUnitOfWork, Depends(get_user_unit_of_work)]) -> UserService:
    return UserService(uow)


def get_professional_information_service(
    uow: Annotated[UserUnitOfWork, Depends(get_user_unit_of_work)],
) -> ProfessionalInformationService:
    return ProfessionalInformationService(uow)


def get_residency_service(uow: Annotated[UserUnitOfWork, Depends(get_user_unit_of_work)]) -> ResidencyService:
    return ResidencyService(uow)


def get_fellowship_service(
    uow: Annotated[UserUnitOfWork, Depends(get_user_unit_of_work)],
) -> FellowshipService:
    return FellowshipService(uow)


def get_username_change_service(
    uow: Annotated[UserUnitOfWork, Depends(get_user_unit_of_work)]
) -> UsernameChangeService:
    return UsernameChangeService(uow)


UserServiceDep = Annotated[UserService, Depends(get_user_service)]
ProfessionalInformationServiceDep = Annotated[
    ProfessionalInformationService, Depends(get_professional_information_service)
]
ResidencyServiceDep = Annotated[ResidencyService, Depends(get_residency_service)]
FellowshipServiceDep = Annotated[FellowshipService, Depends(get_fellowship_service)]
UsernameChangeServiceDep = Annotated[UsernameChangeService, Depends(get_username_change_service)]
