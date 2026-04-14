from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database.base_repository import SQLAlchemyRepository
from app.core.database.base_transaction_manager import SQLAlchemyTransactionManagerBase
from app.core.database.setup_db import session_getter
from app.domains.users.models import (
    CommunicationPreferences,
    Fellowship,
    Job,
    NameChangeRequest,
    ProfessionalInformation,
    Residency,
    User,
)


class UserRepository(SQLAlchemyRepository):
    model = User


class ProfessionalInformationRepository(SQLAlchemyRepository):
    model = ProfessionalInformation


class ResidencyRepository(SQLAlchemyRepository):
    model = Residency


class FellowshipRepository(SQLAlchemyRepository):
    model = Fellowship


class JobRepository(SQLAlchemyRepository):
    model = Job


class NameChangeRequestRepository(SQLAlchemyRepository):
    model = NameChangeRequest


class CommunicationPreferencesRepository(SQLAlchemyRepository):
    model = CommunicationPreferences


class UserTransactionManagerBase(SQLAlchemyTransactionManagerBase):
    def __init__(self, session=None):
        super().__init__(session)
        self.user_repository = UserRepository(self._session)
        self.professional_information_repository = ProfessionalInformationRepository(self._session)
        self.residency_repository = ResidencyRepository(self._session)
        self.fellowship_repository = FellowshipRepository(self._session)
        self.job_repository = JobRepository(self._session)
        self.name_change_request_repository = NameChangeRequestRepository(self._session)
        self.communication_preferences_repository = CommunicationPreferencesRepository(self._session)


def get_user_unit_of_work(session: Annotated[AsyncSession, Depends(session_getter)]) -> UserTransactionManagerBase:
    return UserTransactionManagerBase(session)
