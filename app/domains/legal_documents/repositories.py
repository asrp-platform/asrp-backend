from app.core.database.base_repository import SQLAlchemyRepository
from app.domains.legal_documents.models import Sponsor


class SponsorRepository(SQLAlchemyRepository):
    model = Sponsor
