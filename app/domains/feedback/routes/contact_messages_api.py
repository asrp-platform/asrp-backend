from fastapi import APIRouter

from app.domains.feedback.schemas import (
    ContactMessageResponseSchema,
    CreateContactMessageSchema,
)
from app.domains.feedback.use_cases import CreateContactMessageUseCaseDep


router = APIRouter(prefix="/contact-messages", tags=["Contact Messages"])


@router.post(
    "",
    summary="Create a contact message",
    status_code=201,
)
async def create_contact_message(
    use_case: CreateContactMessageUseCaseDep,
    message_data: CreateContactMessageSchema,
) -> ContactMessageResponseSchema:
    return await use_case.execute(message_data)
