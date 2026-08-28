from datetime import datetime, timezone
from enum import Enum

from pydantic import BaseModel, ConfigDict, model_validator
from pydantic_core import PydanticCustomError

from app.core.database.mixins import UCIMixinSchema
from app.domains.memberships.schemas.membership_types import MembershipTypeSchema
from app.domains.users.schemas.profiles import UserShortSchema


class UserMembershipBoundedSchema(UCIMixinSchema):
    user_id: int
    membership_request_id: int
    membership_type_id: int
    is_active: bool
    expires_at: datetime
    membership_type_id: int
    membership_type: MembershipTypeSchema
    user: UserShortSchema

    terminated: bool
    termination_reason: str | None
    terminated_at: datetime | None

    suspended_until: datetime | None
    suspension_reason: str | None
    suspended_at: datetime | None

    is_suspended: bool

    model_config = ConfigDict(from_attributes=True)


class UserMembershipSchema(UCIMixinSchema):
    expires_at: datetime
    user_id: int
    membership_request_id: int

    is_active: bool

    terminated: bool
    termination_reason: str | None
    terminated_at: datetime | None

    suspended_until: datetime | None
    suspension_reason: str | None
    suspended_at: datetime | None

    is_suspended: bool

    membership_type_id: int
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


class MembershipConfirmationSchema(BaseModel):
    member_name: str
    membership_type: str
    membership_id: str
    valid_through: datetime


class MembershipStatusEnum(str, Enum):
    ACTIVE = "ACTIVE"
    EXPIRED = "EXPIRED"
    SUSPENDED = "SUSPENDED"
    TERMINATED = "TERMINATED"


class MembershipHistoryEventTypeEnum(str, Enum):
    ACTIVATED = "ACTIVATED"
    RENEWED = "RENEWED"
    TYPE_CHANGED = "TYPE_CHANGED"
    SUSPENDED = "SUSPENDED"
    TERMINATED = "TERMINATED"


class MembershipHistoryEventSchema(BaseModel):
    event_type: MembershipHistoryEventTypeEnum
    occurred_at: datetime
    membership_type: str | None = None
    previous_membership_type: str | None = None
    previous_valid_through: datetime | None = None
    valid_through: datetime | None = None
    suspended_until: datetime | None = None
    reason: str | None = None


class MembershipConfirmationReportSchema(BaseModel):
    member_name: str
    membership_type: str
    membership_id: str
    status: MembershipStatusEnum
    member_since: datetime
    valid_through: datetime
    issued_at: datetime
    history: list[MembershipHistoryEventSchema]
