from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, ConfigDict, EmailStr, Field, model_validator

from app.core.database.mixins import UCIMixinSchema
from app.domains.feedback.models import ContactMessageTypeEnum, DonationTypeEnum


class GetInvolvedMessage(BaseModel):
    current_role: str | None = None
    institution_location: str | None = None
    areas: list[str] = []
    ideas: str | None = None
    future_committee_working: bool
    future_leadership_positions: bool
    receive_updates: bool
    model_config = ConfigDict(extra="forbid")


class CommitteesGetInvolvedMessage(BaseModel):
    role_affiliation: Annotated[str | None, Field(min_length=2)] = None
    get_involved_message: Annotated[str | None, Field(min_length=10)] = None
    model_config = ConfigDict(extra="forbid")


class ContactMessage(BaseModel):
    subject: Annotated[str | None, Field(min_length=2)] = None
    contact_message: Annotated[str | None, Field(min_length=10)] = None
    model_config = ConfigDict(extra="forbid")


class DonationSponsorshipMessage(BaseModel):
    organization: Annotated[str | None, Field(min_length=2)] = None
    donation_type: DonationTypeEnum
    message: Annotated[str | None, Field(min_length=10)] = None
    model_config = ConfigDict(extra="forbid")


class CreateContactMessageSchema(BaseModel):
    name: str = Field(min_length=2, max_length=256)
    email: EmailStr
    type: ContactMessageTypeEnum
    message_content: ContactMessage | CommitteesGetInvolvedMessage | GetInvolvedMessage | DonationSponsorshipMessage

    @model_validator(mode="after")
    def validate_message_content(self) -> "CreateContactMessageSchema":
        mapping = {
            ContactMessageTypeEnum.CONTACT: ContactMessage,
            ContactMessageTypeEnum.GET_INVOLVED: GetInvolvedMessage,
            ContactMessageTypeEnum.GET_INVOLVED_COMMITTEES: CommitteesGetInvolvedMessage,
            ContactMessageTypeEnum.DONATION_SPONSORSHIP: DonationSponsorshipMessage,
        }
        schema = mapping.get(self.type)
        if schema:
            data = self.message_content if isinstance(self.message_content, dict) else self.message_content.model_dump()
            self.message_content = schema.model_validate(data)
        return self


class ContactMessageResponseSchema(CreateContactMessageSchema):
    id: int
    created_at: datetime
    updated_at: datetime
    answered: bool
    model_config = ConfigDict(from_attributes=True)


class ContactMessageReplyCreate(BaseModel):
    answer: str = Field(min_length=32)


class ContactMessageReplyResponseSchema(UCIMixinSchema):
    contact_message_id: int
    answer: str

    model_config = {"from_attributes": True}


class HearAboutOptionStatsSchema(BaseModel):
    option: str
    count: int
    percentage: float


class HearAboutStatsResponseSchema(BaseModel):
    total_responses: int
    stats: list[HearAboutOptionStatsSchema]


class FeedbackInterestResponseSchema(BaseModel):
    id: int
    user_id: int
    interest_description: str
    tg_username: str | None = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
