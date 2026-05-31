from datetime import datetime, timezone

from pydantic import BaseModel, ConfigDict, model_validator
from pydantic_core import PydanticCustomError

from app.core.database.mixins import UCIMixinSchema
from app.domains.memberships.schemas.schemas import MembershipTypeSchema
from app.domains.users.schemas import UserShortSchema


class UserMembershipBoundedSchema(UCIMixinSchema):
    user_id: int
    membership_request_id: int
    membership_type_id: int
    is_active: bool
    expires_at: datetime
    membership_type_id: int
    membership_type: MembershipTypeSchema
    user_id: int
    user: UserShortSchema

    model_config = ConfigDict(from_attributes=True)


class UserMembershipSchema(UCIMixinSchema):
    expires_at: datetime
    user_id: int
    membership_request_id: int
    membership_type_id: int
    is_active: bool

    membership_type: MembershipTypeSchema

    model_config = ConfigDict(from_attributes=True)


class SuspendMembershipSchema(BaseModel):
    suspended_until: None | datetime = None
    reason: str

    @model_validator(mode="after")
    def validate_suspend_until(self):
        if self.suspended_until is not None and self.suspended_until <= datetime.now(timezone.utc):
            raise PydanticCustomError(
                "invalid_suspended_until",
                "suspended_until must be a future datetime",
            )
        return self
