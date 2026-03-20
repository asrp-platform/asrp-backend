from fastapi import APIRouter

from app.domains.feedback.schemas import (
    ContactMessageResponseSchema,
    CreateContactMessageSchema,
)
from app.domains.feedback.services import FeedbackServiceDep

router = APIRouter(prefix="/contact-messages", tags=["Contact Messages"])


@router.post(
    "",
    status_code=201,
)
async def create_contact_message(
    contact_message_service: FeedbackServiceDep,
    message_data: CreateContactMessageSchema,
) -> ContactMessageResponseSchema:
    contact_message = await contact_message_service.create_contact_message(message_data)
    return ContactMessageResponseSchema.from_orm(contact_message)
