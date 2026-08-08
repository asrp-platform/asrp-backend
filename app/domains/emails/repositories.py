from app.core.database.base_repository import SQLAlchemyRepository
from app.domains.emails.models import EmailTemplate


class EmailTemplatesRepository(SQLAlchemyRepository):
    model = EmailTemplate
