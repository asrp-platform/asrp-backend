from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database.base_repository import SQLAlchemyRepository
from app.core.database.setup_db import session_getter
from app.core.database.unit_of_work import SQLAlchemyUnitOfWork
from app.domains.users.models import CommunicationPreference, Fellowship, ProfessionalInformation, Residency, User


class UserRepository(SQLAlchemyRepository):
    model = User


class ProfessionalInformationRepository(SQLAlchemyRepository):
    model = ProfessionalInformation


class ResidencyRepository(SQLAlchemyRepository):
    model = Residency


class FellowshipRepository(SQLAlchemyRepository):
    model = Fellowship


class CommunicationPreferenceRepository(SQLAlchemyRepository):
    model = CommunicationPreference


class UserUnitOfWork(SQLAlchemyUnitOfWork):
    def __init__(self, session=None):
        super().__init__(session)
        self.user_repository = UserRepository(self._session)
        self.professional_information_repository = ProfessionalInformationRepository(self._session)
        self.residency_repository = ResidencyRepository(self._session)
        self.fellowship_repository = FellowshipRepository(self._session)
        self.communication_preference_repository = CommunicationPreferenceRepository(self._session)


def get_user_unit_of_work(session: Annotated[AsyncSession, Depends(session_getter)]) -> UserUnitOfWork:
    return UserUnitOfWork(session)
