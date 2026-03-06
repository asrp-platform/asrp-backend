from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field
from app.domains.memberships.models import MembershipTypeEnum, ApprovalStatusEnum
from app.domains.users.schemas import UserSchema


class MembershipTypeSchema(BaseModel):
    id: int
    name: str
    type: MembershipTypeEnum
    price_usd: float
    duration: int
    description: Optional[str] = None
    is_purchasable: bool

    model_config = {
        "from_attributes": True,
    }


class UserMembershipSchema(BaseModel):
    id: int
    created_at: datetime
    updated_at: datetime
    approval_status: ApprovalStatusEnum
    current_period_end: Optional[datetime] = None
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
    approval_status: Optional[ApprovalStatusEnum] = Field(None, description="Approval status of the membership")
    current_period_end: Optional[datetime] = Field(None, description="End date of the current period")
    cancel_at_period_end: Optional[bool] = Field(None, description="Whether to cancel at the end of the period")
    auto_renewal: Optional[bool] = Field(None, description="Whether auto-renewal is enabled")
    membership_type_id: Optional[int] = Field(None, description="ID of the membership type")
