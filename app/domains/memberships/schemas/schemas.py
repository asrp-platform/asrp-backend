from datetime import datetime

from pydantic import BaseModel, model_validator
from pydantic_core import PydanticCustomError

from app.domains.memberships.models import MembershipRequestStatusEnum, MembershipTypeEnum
from app.domains.memberships.schemas.membership_types_schemas import MembershipTypeSchema
from app.domains.shared.schemas import FeedbackAdditionalInfoCreateSchema
from app.domains.users.schemas import UserShortSchema


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
    admin_comment: str | None

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


class MembershipDowngradeCreateCreateSchema(BaseModel):
    target_membership_type_id: int
    reason_changing: str


class UserMembershipTypeChangeRequestUpdateAdminSchema(BaseModel):
    approved: bool
    admin_comment: str | None = None

    @model_validator(mode="after")
    def check_rejection_comment(self):
        if self.approved is False and self.admin_comment is None:
            raise PydanticCustomError(
                "admin_comment necessary when rejected",
                "Admin comment is required when rejecting user membership type change request",
            )
        return self
