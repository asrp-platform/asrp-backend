from datetime import datetime, timezone
from typing import Annotated, Any, Generic, Literal, TypeVar
from uuid import uuid4

from fastapi import Depends

from app.core.common.exceptions import NotResourceOwnerError
from app.core.config import settings
from app.core.storage.base_storage import BaseFileStorage
from app.core.storage.storage_factory import FileStorageDep
from app.domains.shared.transaction_managers import TransactionManager, TransactionManagerDep
from app.domains.users.exceptions import (
    CannotDeleteLastResidencyError,
    FellowshipNotFoundError,
    InvalidPasswordError,
    JobNotFoundError,
    NameChangeRequestCooldownNotExpiredError,
    NameChangeRequestNotFoundError,
    PendingNameChangeRequestAlreadyExistsError,
    ProfessionalExperienceCurrentPositionExistsError,
    ResidencyNotFoundError,
    UserNotFoundError,
)
from app.domains.users.models import (
    CommunicationPreferences,
    Fellowship,
    Job,
    NameChangeRequest,
    NameChangeRequestStatusEnum,
    ProfessionalInformation,
    Residency,
    User,
)


class UserService:
    def __init__(self, transaction_manager: TransactionManager, file_storage: BaseFileStorage):
        self.transaction_manager = transaction_manager
        self.file_storage = file_storage

    async def check_resource_owner(self, user_id: int, *, current_user: User):
        """
        Ensures:
        - user exists
        - current user is a resource owner (optional) or admin
        """
        async with self.transaction_manager:
            user = await self.transaction_manager.user_repository.get_first_by_kwargs(id=user_id)
            if user is None:
                raise UserNotFoundError("User with provided ID not found")
            if current_user is None or user_id != current_user.id or not current_user.admin:
                raise NotResourceOwnerError("Not resource owner")

    async def get_all_paginated_counted(
        self, limit: int = None, offset: int = None, order_by: str = None, filters: dict[str, Any] = None
    ) -> [list[User], int]:
        async with self.transaction_manager:
            return await self.transaction_manager.user_repository.list(limit, offset, order_by, filters)

    async def get_all_users_count(self) -> int:
        async with self.transaction_manager:
            return await self.transaction_manager.user_repository.get_count()

    async def create(self, **kwargs):
        async with self.transaction_manager:
            return await self.transaction_manager.user_repository.create(**kwargs)

    async def get_user_by_kwargs(self, **kwargs) -> User:
        async with self.transaction_manager:
            return await self.transaction_manager.user_repository.get_first_by_kwargs(**kwargs)

    async def update_user(self, user_id: int, **kwargs) -> User:
        user = await self.transaction_manager.user_repository.get_first_by_kwargs(id=user_id)
        if user is None:
            raise UserNotFoundError("User with provided ID not found")
        await self.transaction_manager.user_repository.update(user_id, **kwargs)
        return user

    async def get_user_avatar_url(self, user_id: int):
        async with self.transaction_manager:
            user = await self.transaction_manager.user_repository.get_first_by_kwargs(id=user_id)
            if user is None:
                raise UserNotFoundError("User with provided ID not found")
            avatar_object_key = user.avatar_path
            if avatar_object_key is None:
                return None
        return await self.file_storage.get_file_url(avatar_object_key)

    async def upload_avatar(self, user_id: int, file):
        try:
            filename = f"avatars/{uuid4()}.{file.filename.split('.')[-1]}"
            file_content = await file.read()
            upload_result = await self.file_storage.upload_file(
                filename,
                file_content
            )
            async with self.transaction_manager:
                await self.transaction_manager.user_repository.update(user_id, avatar_path=filename)
            return upload_result
        except Exception as e:
            raise e

    async def delete_user_avatar(self, user_id: int) -> None:
        async with self.transaction_manager:
            user = await self.transaction_manager.user_repository.get_first_by_kwargs(id=user_id)
            if user is None:
                raise UserNotFoundError("User with provided ID not found")
            await self.transaction_manager.user_repository.update(user_id, avatar_path=None)

    async def change_password(
        self,
        user_id: int,
        old_password: str,
        new_password: str,
    ):
        user = await self.transaction_manager.user_repository.get_first_by_kwargs(id=user_id)

        if user is None:
            raise UserNotFoundError("user with provided email not found")

        if not user.verify_password(old_password):
            raise InvalidPasswordError("Invalid password")

        user.password = new_password
        await self.transaction_manager._session.flush()  # noqa property's setter manual calling
        await self.transaction_manager.user_repository.update(
            user.id, last_password_change=datetime.now(tz=timezone.utc)
        )


class ProfessionalInformationService:
    def __init__(self, transaction_manager: TransactionManager):
        self.transaction_manager = transaction_manager

    async def get_by_user_id(self, user_id: int) -> ProfessionalInformation | None:
        async with self.transaction_manager:
            user = await self.transaction_manager.user_repository.get_first_by_kwargs(id=user_id)
            if user is None:
                raise UserNotFoundError("User with provided ID not found")
            return await self.transaction_manager.professional_information_repository.get_first_by_kwargs(
                user_id=user_id
            )

    async def create_or_update(self, user_id: int, current_user_id: int, **kwargs) -> ProfessionalInformation:
        if user_id != current_user_id:
            raise NotResourceOwnerError("Not resource owner")

        async with self.transaction_manager:
            user = await self.transaction_manager.user_repository.get_first_by_kwargs(id=user_id)

            if user is None:
                raise UserNotFoundError("User with provided ID not found")

            professional_information = (
                await self.transaction_manager.professional_information_repository.get_first_by_kwargs(user_id=user_id)
            )
            data = {**kwargs, "user_id": user.id}

            if professional_information is not None:
                return await self.transaction_manager.professional_information_repository.update(
                    professional_information.id, **data
                )
            else:
                return await self.transaction_manager.professional_information_repository.create(**data)


ProfessionalExperienceT = TypeVar("ProfessionalExperienceT")


class BaseUserOwnedService(Generic[ProfessionalExperienceT]):
    def __init__(self, transaction_manager: TransactionManager):
        self.transaction_manager = transaction_manager

    @property
    def _repository(self):
        raise NotImplementedError

    @property
    def _not_found_error(self):
        raise NotImplementedError

    @property
    def _entity_name(self) -> str:
        raise NotImplementedError

    async def _check_resource_owner(
        self,
        user_id: int,
        *,
        current_user_id: int | None = None,
        resource_id: int | None = None,
    ) -> None:
        user = await self.transaction_manager.user_repository.get_first_by_kwargs(id=user_id)

        if user is None:
            raise UserNotFoundError("User with provided ID not found")

        if current_user_id is not None and user_id != current_user_id:
            raise NotResourceOwnerError("Not resource owner")

        if resource_id is not None:
            resource = await self._repository.get_first_by_kwargs(id=resource_id, user_id=user_id)
            if resource is None:
                raise self._not_found_error(f"{self._entity_name} with provided ID not found")

    async def list_for_user(self, user_id: int) -> list[ProfessionalExperienceT]:
        async with self.transaction_manager:
            await self._check_resource_owner(user_id)
            return await self._repository.get_all_by_kwargs(user_id=user_id)

    async def get_for_user(self, user_id: int, resource_id: int) -> ProfessionalExperienceT:
        async with self.transaction_manager:
            await self._check_resource_owner(user_id, resource_id=resource_id)
            return await self._repository.get_first_by_kwargs(id=resource_id, user_id=user_id)

    async def create_for_user(self, user_id: int, current_user_id: int, **kwargs) -> ProfessionalExperienceT:
        async with self.transaction_manager:
            await self._check_resource_owner(user_id, current_user_id=current_user_id)
            return await self._repository.create(user_id=user_id, **kwargs)

    async def update_for_user(
        self,
        user_id: int,
        current_user_id: int,
        resource_id: int,
        update_data: dict,
    ) -> ProfessionalExperienceT:
        async with self.transaction_manager:
            await self._check_resource_owner(user_id, current_user_id=current_user_id, resource_id=resource_id)
            return await self._repository.update(resource_id, **update_data)

    async def delete_for_user(
        self,
        user_id: int,
        current_user_id: int,
        resource_id: int,
    ) -> int:
        async with self.transaction_manager:
            await self._check_resource_owner(user_id, current_user_id=current_user_id, resource_id=resource_id)
            return await self._repository.mark_as_deleted(resource_id)


class ProfessionalExperienceBaseService(BaseUserOwnedService[ProfessionalExperienceT]):
    async def create_for_user(self, user_id: int, current_user_id: int, **kwargs) -> ProfessionalExperienceT:
        async with self.transaction_manager:
            await self._check_resource_owner(user_id, current_user_id=current_user_id)

            if kwargs.get("current_position"):
                await self._check_current_position_selected(user_id)

            return await self._repository.create(user_id=user_id, **kwargs)

    async def update_for_user(
        self,
        user_id: int,
        current_user_id: int,
        resource_id: int,
        update_data: dict,
    ) -> ProfessionalExperienceT:
        async with self.transaction_manager:
            await self._check_resource_owner(user_id, current_user_id=current_user_id, resource_id=resource_id)

            if update_data.get("current_position"):
                await self._check_current_position_selected(user_id)

            return await self._repository.update(resource_id, **update_data)

    async def _check_current_position_selected(self, user_id: int) -> None:
        residency = await self.transaction_manager.residency_repository.get_first_by_kwargs(
            user_id=user_id, current_position=True
        )
        fellowship = await self.transaction_manager.fellowship_repository.get_first_by_kwargs(
            user_id=user_id, current_position=True
        )
        job = await self.transaction_manager.job_repository.get_first_by_kwargs(user_id=user_id, current_position=True)

        if residency is not None or fellowship is not None or job is not None:
            raise ProfessionalExperienceCurrentPositionExistsError("Current position has already been selected")


class ResidencyService(ProfessionalExperienceBaseService[Residency]):
    @property
    def _repository(self):
        return self.transaction_manager.residency_repository

    @property
    def _not_found_error(self):
        return ResidencyNotFoundError

    @property
    def _entity_name(self) -> str:
        return "Residency"

    async def delete_for_user(self, user_id: int, current_user_id: int, resource_id: int) -> int:
        async with self.transaction_manager:
            await self._check_resource_owner(user_id, current_user_id=current_user_id, resource_id=resource_id)

            remaining = await self._repository.get_count(user_id=user_id)

            if remaining <= 1:
                raise CannotDeleteLastResidencyError("Cannot delete last residency for user")

            await self._repository.mark_as_deleted(resource_id)
            return resource_id


class FellowshipService(ProfessionalExperienceBaseService[Fellowship]):
    @property
    def _repository(self):
        return self.transaction_manager.fellowship_repository

    @property
    def _not_found_error(self):
        return FellowshipNotFoundError

    @property
    def _entity_name(self) -> str:
        return "Fellowship"


class JobService(ProfessionalExperienceBaseService[Job]):
    @property
    def _repository(self):
        return self.transaction_manager.job_repository

    @property
    def _not_found_error(self):
        return JobNotFoundError

    @property
    def _entity_name(self) -> str:
        return "Job"


class NameChangeRequestService:
    def __init__(self, transaction_manager: TransactionManager):
        self.transaction_manager = transaction_manager

    async def check_resource_existence(
        self,
        user_id: int,
        *,
        current_user_id: int | None = None,
        name_change_request_id: int | None = None,
    ) -> None:
        async with self.transaction_manager:
            user = await self.transaction_manager.user_repository.get_first_by_kwargs(id=user_id)

            if user is None:
                raise UserNotFoundError("User with provided ID not found")

            if current_user_id is not None and user_id != current_user_id:
                raise NotResourceOwnerError("Not resource owner")

            if name_change_request_id is not None:
                name_change_request = await self.transaction_manager.name_change_request_repository.get_first_by_kwargs(
                    id=name_change_request_id, user_id=user_id
                )
                if name_change_request is None:
                    raise NameChangeRequestNotFoundError("Name change request with provided ID not found")

    async def get_pending_name_change_request(self, user_id: int, name_change_request_id: int) -> NameChangeRequest:
        await self.check_resource_existence(user_id, name_change_request_id=name_change_request_id)

        async with self.transaction_manager:
            return await self.transaction_manager.name_change_request_repository.get_first_by_kwargs(
                id=name_change_request_id, status=NameChangeRequestStatusEnum.PENDING
            )

    async def get_all_paginated_counted_name_change_requests(
        self, limit: int = None, offset: int = None, order_by: str = None, filters: dict[str, Any] = None
    ) -> list[NameChangeRequest]:
        async with self.transaction_manager:
            return await self.transaction_manager.name_change_request_repository.list(limit, offset, order_by, filters)

    async def get_last_name_change_request_by_user_id(self, user_id: int) -> NameChangeRequest | None:
        async with self.transaction_manager:
            name_change_request, _ = await self.transaction_manager.name_change_request_repository.list(
                filters={"user_id": user_id},
                limit=1,
                order_by="-created_at",
            )

            if name_change_request:
                return name_change_request[0]
            return None

    async def create_name_change_request(self, user_id: int, **kwargs) -> NameChangeRequest:
        user = await self.transaction_manager.user_repository.get_first_by_kwargs(id=user_id)
        if user is None:
            raise UserNotFoundError("User with provided ID not found")

        name_change_request = await self.get_last_name_change_request_by_user_id(user_id=user_id)

        if name_change_request is not None and name_change_request.status == NameChangeRequestStatusEnum.PENDING:
            raise PendingNameChangeRequestAlreadyExistsError(
                "Pending name change request for User with provided ID is already exists"
            )

        cooldown = settings.NAME_CHANGE_REQUEST_COOLDOWN_DAYS
        if name_change_request is not None and cooldown is not None and user.last_name_change is not None:
            days_elapsed = (datetime.now(tz=timezone.utc) - user.last_name_change).days

            if days_elapsed < cooldown:
                raise NameChangeRequestCooldownNotExpiredError(
                    "The time until the next name change request for User with provided ID has not passed yet"
                )

        return await self.transaction_manager.name_change_request_repository.create(user_id=user_id, **kwargs)

    async def update_name_change_request(
        self,
        user_id: int,
        name_change_request_id: int,
        action: Literal["approve", "reject"],
        reason_rejecting: str | None,
    ) -> None:
        if action == "approve":
            await self._approve_name_change_request(user_id, name_change_request_id)
        if action == "reject":
            await self._reject_name_change_request(user_id, name_change_request_id, reason_rejecting)

    async def _approve_name_change_request(self, user_id: int, name_change_request_id: int) -> None:
        await self.check_resource_existence(user_id, name_change_request_id=name_change_request_id)

        async with self.transaction_manager:
            name_change_request = await self.transaction_manager.name_change_request_repository.get_first_by_kwargs(
                id=name_change_request_id
            )

            await self.transaction_manager.user_repository.update(
                user_id,
                firstname=name_change_request.firstname,
                lastname=name_change_request.lastname,
                middlename=name_change_request.middlename,
                last_name_change=datetime.now(tz=timezone.utc),
            )

            await self.transaction_manager.name_change_request_repository.update(
                name_change_request_id, status=NameChangeRequestStatusEnum.APPROVED
            )

    async def _reject_name_change_request(
        self, user_id: int, name_change_request_id: int, reason_rejecting: str
    ) -> None:
        await self.check_resource_existence(user_id, name_change_request_id=name_change_request_id)

        async with self.transaction_manager:
            await self.transaction_manager.name_change_request_repository.update(
                name_change_request_id,
                reason_rejecting=reason_rejecting,
                status=NameChangeRequestStatusEnum.REJECTED,
            )


class CommunicationPreferencesService:
    def __init__(self, transaction_manager):
        self.transaction_manager = transaction_manager

    async def check_resource_owner(self, user_id: int, *, current_user_id: int = None):
        user = await self.transaction_manager.user_repository.get_first_by_kwargs(id=user_id)

        if user is None:
            raise UserNotFoundError("User with provided ID not found")

        if current_user_id is not None and user_id != current_user_id:
            raise NotResourceOwnerError("Not resource owner")

    async def get_or_create(self, user_id: int, is_agrees_communications: bool = False) -> CommunicationPreferences:
        """
        Retrieves communication settings for the user or creates them with default values.
        This ensures that the user always has the settings after calling the method.
        """
        user = await self.transaction_manager.user_repository.get_first_by_kwargs(id=user_id)

        if user is None:
            raise UserNotFoundError("User with provided ID not found")

        communication_preferences = (
            await self.transaction_manager.communication_preferences_repository.get_first_by_kwargs(user_id=user_id)
        )

        if not communication_preferences:
            create_data = {"user_id": user_id}
            if is_agrees_communications:
                create_data.update(
                    {
                        "newsletters": True,
                        "events_meetings": True,
                        "committees_leadership": True,
                        "volunteer_opportunities": True,
                    }
                )

            communication_preferences = await self.transaction_manager.communication_preferences_repository.create(
                **create_data
            )

        return communication_preferences

    async def update_or_create_preferences(
        self,
        user_id: int,
        update_data: dict | None = None,
        is_agrees_communications: bool = False,
    ) -> CommunicationPreferences:
        if update_data is None:
            update_data = {}

        communication_preferences = (
            await self.transaction_manager.communication_preferences_repository.get_first_by_kwargs(user_id=user_id)
        )

        if not communication_preferences:
            create_data = {"user_id": user_id}
            if is_agrees_communications:
                create_data.update(
                    {
                        "newsletters": True,
                        "events_meetings": True,
                        "committees_leadership": True,
                        "volunteer_opportunities": True,
                    }
                )

            return await self.transaction_manager.communication_preferences_repository.create(**create_data)

        return await self.transaction_manager.communication_preferences_repository.update(
            communication_preferences.id, **update_data
        )


def get_user_service(
    transaction_manager: TransactionManagerDep,
    file_storage: FileStorageDep,
) -> UserService:
    return UserService(transaction_manager, file_storage)


def get_professional_information_service(
    transaction_manager: TransactionManagerDep,
) -> ProfessionalInformationService:
    return ProfessionalInformationService(transaction_manager)


def get_residency_service(
    transaction_manager: TransactionManagerDep,
) -> ResidencyService:
    return ResidencyService(transaction_manager)


def get_fellowship_service(
    transaction_manager: TransactionManagerDep,
) -> FellowshipService:
    return FellowshipService(transaction_manager)


def get_job_service(
    transaction_manager: TransactionManagerDep,
) -> JobService:
    return JobService(transaction_manager)


def get_name_change_request_service(transaction_manager: TransactionManagerDep) -> NameChangeRequestService:
    return NameChangeRequestService(transaction_manager)


def get_communication_preferences_service(
    transaction_manager: TransactionManagerDep,
) -> CommunicationPreferencesService:
    return CommunicationPreferencesService(transaction_manager)


UserServiceDep = Annotated[UserService, Depends(get_user_service)]
ProfessionalInformationServiceDep = Annotated[
    ProfessionalInformationService, Depends(get_professional_information_service)
]
ResidencyServiceDep = Annotated[ResidencyService, Depends(get_residency_service)]
FellowshipServiceDep = Annotated[FellowshipService, Depends(get_fellowship_service)]
JobServiceDep = Annotated[JobService, Depends(get_job_service)]
NameChangeRequestServiceDep = Annotated[NameChangeRequestService, Depends(get_name_change_request_service)]
CommunicationPreferencesServiceDep = Annotated[
    CommunicationPreferencesService, Depends(get_communication_preferences_service)
]
