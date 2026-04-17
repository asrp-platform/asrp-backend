from app.core.database.base_repository import SQLAlchemyRepository
from app.domains.feedback.models import ContactMessage, ContactMessageReply, FeedbackAdditionalInfo


class ContactMessageRepository(SQLAlchemyRepository[ContactMessage]):
    model = ContactMessage


class FeedbackAdditionalInfoRepository(SQLAlchemyRepository):
    model = FeedbackAdditionalInfo


class ContactMessageReplyRepository(SQLAlchemyRepository):
    model = ContactMessageReply
