from datetime import datetime

from pydantic import BaseModel, Field

from app.domains.memberships.models import MembershipRequestStatusEnum, MembershipTypeEnum
from app.domains.shared.schemas import FeedbackAdditionalInfoCreateSchema


class MembershipTypeSchema(BaseModel):
    id: int
    name: str
    type: MembershipTypeEnum
    price_usd: float
    duration: int
    description: str | None = None
    is_purchasable: bool

    model_config = {
        "from_attributes": True,
    }


class MembershipRequestDataSchema(BaseModel):
    primary_affiliation: str
    job_title: str
    practice_setting: str
    subspecialty: str


class MembershipRequestCreateSchema(BaseModel):
    membership: MembershipRequestDataSchema
    membership_type: MembershipTypeEnum
    feedback_additional_info: FeedbackAdditionalInfoCreateSchema
    is_agrees_communications: bool

    model_config = {
        "from_attributes": True,
    }


class MembershipRequestSchema(BaseModel):
    id: int
    created_at: datetime
    updated_at: datetime
    status: MembershipRequestStatusEnum
    current_period_end: datetime | None = None
    user_id: int
    membership_type_id: int

    model_config = {
        "from_attributes": True,
    }


class UserMembershipViewSchema(MembershipRequestSchema):
    membership_type: MembershipTypeSchema


class UserMembershipMockUpdateSchema(BaseModel):
    status: MembershipRequestStatusEnum = Field(
        default=MembershipRequestStatusEnum.PAYMENT_PENDING,
        description="Approval status of the membership",
    )
    current_period_end: datetime | None = Field(None, description="End date of the current period")
    membership_type: MembershipTypeEnum = Field(
        default=MembershipTypeEnum.ACTIVE,
        description="Membership type",
    )
