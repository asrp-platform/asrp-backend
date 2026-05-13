from datetime import datetime

from pydantic import BaseModel, model_validator
from pydantic_core import PydanticCustomError

from app.core.database.mixins import UCIMixinSchema
from app.domains.memberships.models import MembershipRequestStatusEnum, MembershipTypeEnum
from app.domains.shared.schemas import FeedbackAdditionalInfoCreateSchema
from app.domains.users.schemas import UserShortSchema


class MembershipTypeShortSchema(BaseModel):
    id: int
    name: str
    type: MembershipTypeEnum


class MembershipTypeSchema(MembershipTypeShortSchema):
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


class MembershipRequestReapplySchema(MembershipRequestDataSchema):
    membership_type_id: int


class MembershipRequestViewSchema(MembershipRequestDataSchema):
    id: int
    created_at: datetime
    updated_at: datetime
    status: MembershipRequestStatusEnum
    current_period_end: datetime | None = None
    user_id: int
    user: UserShortSchema
    membership_type_id: int
    membership_type: MembershipTypeSchema

    model_config = {
        "from_attributes": True,
    }


class MembershipRequestUpdateAdminSchema(BaseModel):
    status: MembershipRequestStatusEnum
    admin_comment: str | None = None

    @model_validator(mode="after")
    def check_reason_rejecting(self):
        if self.status == MembershipRequestStatusEnum.REJECTED and self.admin_comment is None:
            raise PydanticCustomError(
                "admin_comment necessary when rejected",
                "Admin comment is required when rejecting user membership request",
            )
        return self


class UserMembershipSchema(UCIMixinSchema):
    expires_at: datetime
    user_id: int
    membership_request_id: int
    membership_type_id: int
    is_active: bool

    membership_type: MembershipTypeShortSchema

    model_config = {"from_attributes": True}
