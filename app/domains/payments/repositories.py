from app.core.database.base_repository import SQLAlchemyRepository
from app.domains.payments.models import Payment, ProcessedWebhookEvent


class PaymentRepository(SQLAlchemyRepository):
    model = Payment


class ProcessedWebhookEventRepository(SQLAlchemyRepository):
    model = ProcessedWebhookEvent
