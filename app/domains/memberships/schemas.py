from datetime import datetime

from pydantic import BaseModel, Field

from app.domains.memberships.models import ApprovalStatusEnum, MembershipTypeEnum


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


class UserMembershipSchema(BaseModel):
    id: int
    created_at: datetime
    updated_at: datetime
    approval_status: ApprovalStatusEnum
    current_period_end: datetime | None = None
    cancel_at_period_end: bool
    auto_renewal: bool
    has_access: bool
    user_id: int
    membership_type_id: int

    model_config = {
        "from_attributes": True,
    }


class UserMembershipOut(UserMembershipSchema):
    membership_type: MembershipTypeSchema


class UpdateUserMembershipMockIn(BaseModel):
    approval_status: ApprovalStatusEnum = Field(
        default=ApprovalStatusEnum.PENDING,
        description="Approval status of the membership",
    )
    current_period_end: datetime | None = Field(None, description="End date of the current period")
    cancel_at_period_end: bool = Field(False, description="Whether to cancel at the end of the period")
    auto_renewal: bool = Field(True, description="Whether auto-renewal is enabled")
    membership_type: MembershipTypeEnum = Field(
        default=MembershipTypeEnum.ACTIVE,
        description="Type of the membership",
    )
