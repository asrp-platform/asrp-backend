from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator, model_validator
from pydantic_core import PydanticCustomError

from app.core.database.mixins import UCIMixinSchema
from app.domains.feedback.constants import HEAR_ABOUT_ASRP_OPTIONS
from app.domains.feedback.models import ContactMessageTypeEnum, DonationTypeEnum


class FeedbackAdditionalInfoCreateSchema(BaseModel):
    hear_about_asrp: str
    tg_username: str | None = None
    interest_description: str | None = None

    model_config = {"from_attributes": True}

    @field_validator("hear_about_asrp")
    def hear_about_asrp_validator(cls, value: str) -> str:
        normalized = value.strip()
        if normalized not in HEAR_ABOUT_ASRP_OPTIONS:
            raise PydanticCustomError("invalid_hear_about_asrp", "Invalid value for hear_about_asrp")
        return normalized

    @field_validator("tg_username")
    def tg_username_validator(cls, value):
        if value is None:
            return value
        value = value.strip()
        if not value:
            return None
        if not value.startswith("@"):
            raise PydanticCustomError("invalid_telegram_username", "Telegram username must start with '@'")
        username = value[1:]
        if len(username) < 5 or len(username) > 32:
            raise PydanticCustomError(
                "invalid_telegram_username",
                "Telegram username must be at least 5 and less than 32 characters",
            )
        return username


class AnswerContactMessageSchema(BaseModel):
    subject: str
    answer_message: str


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
    get_involved_message: str | None = None
    model_config = ConfigDict(extra="forbid")


class ContactMessage(BaseModel):
    subject: Annotated[str | None, Field(min_length=2)] = None
    contact_message: str | None = None
    model_config = ConfigDict(extra="forbid")


class DonationSponsorshipMessage(BaseModel):
    organization: Annotated[str | None, Field(min_length=2)] = None
    donation_type: DonationTypeEnum
    message: str
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
