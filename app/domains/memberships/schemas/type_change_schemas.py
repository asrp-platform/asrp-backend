from pydantic import BaseModel, ConfigDict

from app.core.database.mixins import UCIMixinSchema
from app.domains.memberships.models import MembershipTypeEnum


class BoundedMembershipTypeSchema(BaseModel):
    id: int
    name: str
    type: MembershipTypeEnum


class BoundedUserSchema(BaseModel):
    id: int
    email: str


class BoundedUserMembershipSchema(BaseModel):
    is_active: bool

    user_id: int
    user: BoundedUserSchema

    membership_type_id: int
    membership_type: BoundedMembershipTypeSchema

    model_config = {"from_attributes": True}


class UserMembershipTypeChangeRequestViewSchema(UCIMixinSchema):
    target_membership_type_id: int
    target_membership_type: BoundedMembershipTypeSchema
    user_membership_id: int
    user_membership: BoundedUserMembershipSchema
    upgrade: bool
    reason_changing: str
    approved: bool
    admin_comment: str | None
    pending: bool

    model_config = ConfigDict(from_attributes=True)
