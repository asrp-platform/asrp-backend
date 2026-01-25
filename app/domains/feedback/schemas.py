from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, EmailStr, Field

from app.domains.feedback.models import ContactMessageTypeEnum


class GetInvolvedMessage(BaseModel):
    current_role: str | None = None
    institution_location: str | None = None
    areas: list[str] = []
    ideas: str | None = None
    future_committee_working: bool
    future_leadership_positions: bool
    receive_updates: bool


class CommitteesGetInvolvedMessage(BaseModel):
    role_affiliation: Annotated[str | None, Field(min_length=2)] = None
    get_involved_message: Annotated[str | None, Field(min_length=10)] = None


class ContactMessage(BaseModel):
    subject: Annotated[str | None, Field(min_length=2)] = None
    contact_message: Annotated[str | None, Field(min_length=10)] = None


class CreateContactMessageSchema(BaseModel):
    name: str = Field(min_length=2, max_length=256)
    email: EmailStr
    type: ContactMessageTypeEnum
    message_content: ContactMessage | CommitteesGetInvolvedMessage | GetInvolvedMessage


class ContactMessageResponseSchema(CreateContactMessageSchema):
    id: int
    created_at: datetime
    updated_at: datetime
    answered: bool

    model_config = {
        "from_attributes": True,
    }
