from app.core.database.base_repository import SQLAlchemyRepository
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
