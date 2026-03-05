
from pydantic import BaseModel, Field

from app.domains.memberships.enums import MembershipTypeEnum
from app.domains.shared.schemas import AdditionalDetailCreateSchema


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


class MembershipCreateSchema(BaseModel):
    primary_affiliation: str
    job_title: str
    practice_setting: str
    subspecialty: str
    is_trained_in_us: bool


class MembershipDataSchema(BaseModel):
    membership: MembershipCreateSchema
    membership_type: MembershipTypeEnum
    additional_detail: AdditionalDetailCreateSchema
    is_agrees_communications: bool

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
