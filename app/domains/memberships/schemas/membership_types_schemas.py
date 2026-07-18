from typing import Literal

from pydantic import BaseModel, ConfigDict, model_validator
from pydantic_core import PydanticCustomError

from app.core.database.mixins import UCIMixinSchema
from app.domains.memberships.models import MembershipTypeEnum


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


class UpdateMembershipTypeSchema(BaseModel):
    name: str | None = None
    description: str | None = None
    price_usd: int | None = None


class BoundedUserSchema(BaseModel):
    id: int
    email: str


class BoundedUserMembershipSchema(BaseModel):
    is_active: bool

    user_id: int
    user: BoundedUserSchema

    membership_type_id: int
    membership_type: MembershipTypeShortSchema

    model_config = {"from_attributes": True}


class UserMembershipTypeChangeRequestProfileSchema(UCIMixinSchema):
    target_membership_type_id: int
    target_membership_type: MembershipTypeShortSchema
    user_membership_id: int
    reason_changing: str
    approved: bool
    admin_comment: str | None
    pending: bool

    model_config = ConfigDict(from_attributes=True)


class UserMembershipTypeChangeRequestViewSchema(UserMembershipTypeChangeRequestProfileSchema):
    user_membership: BoundedUserMembershipSchema


class ReviewedMembershipTypeChangeRequestSchema(UCIMixinSchema):
    target_membership_type_id: int
    user_membership_id: int
    reason_changing: str
    approved: bool
    admin_comment: str | None
    pending: bool

    model_config = ConfigDict(from_attributes=True)


class ReviewMembershipTypeChangeRequest(BaseModel):
    action: Literal["approve", "reject"]
    admin_comment: str | None = None

    @model_validator(mode="after")
    def check_reason_rejecting(self):
        if self.action == "reject" and self.admin_comment is None:
            raise PydanticCustomError(
                "admin_comment necessary when rejected",
                "Admin comment is required when rejecting user membership downgrade request",
            )
        return self
