from datetime import datetime

from pydantic import BaseModel, Field

from app.domains.memberships.models import ApprovalStatusEnum, MembershipTypeEnum
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


class MembershipDataSchema(BaseModel):
    primary_affiliation: str
    job_title: str
    practice_setting: str
    subspecialty: str
    is_trained_in_us: bool


class MembershipCreateSchema(BaseModel):
    membership: MembershipDataSchema
    membership_type: MembershipTypeEnum
    feedback_additional_info: FeedbackAdditionalInfoCreateSchema
    is_agrees_communications: bool

    model_config = {
        "from_attributes": True,
    }


class UserMembershipSchema(BaseModel):
    id: int
    created_at: datetime
    updated_at: datetime
    approval_status: ApprovalStatusEnum
    current_period_end: datetime | None = None
    auto_renewal: bool
    has_access: bool
    user_id: int
    membership_type_id: int

    model_config = {
        "from_attributes": True,
    }


class UserMembershipViewSchema(UserMembershipSchema):
    membership_type: MembershipTypeSchema


class UserMembershipMockUpdateSchema(BaseModel):
    approval_status: ApprovalStatusEnum = Field(
        default=ApprovalStatusEnum.PENDING,
        description="Approval status of the membership",
    )
    current_period_end: datetime | None = Field(None, description="End date of the current period")
    auto_renewal: bool = Field(True, description="Whether auto-renewal is enabled")
    membership_type: MembershipTypeEnum = Field(
        default=MembershipTypeEnum.ACTIVE,
        description="Type of the membership",
    )
