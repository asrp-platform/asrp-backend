from datetime import datetime
from typing import Annotated, Literal

import phonenumbers
from pydantic import AliasPath, BaseModel, ConfigDict, Field, field_validator, model_validator
from pydantic_core import PydanticCustomError

from app.core.database.mixins import UCIMixinSchema
from app.domains.auth.schemas import US_COUNTRY_VALUES
from app.domains.memberships.models import MembershipTypeEnum
from app.domains.shared.types import Password
from app.domains.users.models import NameChangeRequestStatusEnum


class UserShortSchema(BaseModel):
    id: int
    email: str


class UserPublicSchema(BaseModel):
    id: int
    firstname: str
    middlename: str | None
    lastname: str
    preferred_name: str | None
    suffix: str | None
    credentials: str | None
    email: str
    admin: bool
    superuser: bool
    banned: bool
    ban_reason: str | None
    description: str | None
    country: str
    state: str | None
    city: str
    languages_spoken: str | None
    professional_interests: str | None
    avatar_url: str | None

    model_config = ConfigDict(from_attributes=True)


class MemberDirectorySchema(BaseModel):
    id: int
    firstname: str
    middlename: str | None
    lastname: str
    preferred_name: str | None
    suffix: str | None
    credentials: str | None
    description: str | None
    country: str
    state: str | None
    city: str
    languages_spoken: str | None
    professional_interests: str | None
    avatar_url: str | None
    membership_type: MembershipTypeEnum = Field(validation_alias=AliasPath("membership", "membership_type", "type"))

    model_config = ConfigDict(from_attributes=True)


class UserPrivateSchema(UserPublicSchema):
    telegram_username: str | None
    avatar_path: str | None
    phone_number: str | None
    pending: bool
    created_at: datetime
    last_password_change: datetime | None
    postal_code: str | None = None


class UpdateUserByAdminSchema(BaseModel):
    admin: bool | None = Field(None, description="Grant or revoke admin role for user")


class BanUserSchema(BaseModel):
    ban_reason: str = Field(..., max_length=512, description="Reason for banning the user")


class UpdateUserSchema(BaseModel):
    preferred_name: str | None = None
    suffix: str | None = None
    credentials: str | None = None
    description: str | None = None
    country: str | None = Field(None, min_length=2)
    state: str | None = None
    postal_code: str | None = None
    city: str | None = Field(None, min_length=2)
    languages_spoken: str | None = None
    professional_interests: str | None = None
    telegram_username: str | None = None
    phone_number: Annotated[str | None, Field()] = None

    @model_validator(mode="after")
    def check_us_address_fields(self):
        if self.country is None:
            return self
        if self.country.strip().upper() in US_COUNTRY_VALUES:
            if not self.state or not self.state.strip():
                raise PydanticCustomError("state_required", "State is required for USA")
            if not self.postal_code or not self.postal_code.strip():
                raise PydanticCustomError("postal_code_required", "Postal code is required for USA")
        return self

    @field_validator("country", "city")
    def forbid_null_for_required_fields(cls, value, info):
        if value is None:
            raise PydanticCustomError("field_null", "{field_name} cannot be null", {"field_name": info.field_name})
        return value

    @field_validator("preferred_name", mode="before")
    def normalize_preferred_name(cls, value):
        return None if value == "" else value

    @field_validator("phone_number")
    def validate_phone_number(cls, value):
        if value is None or value.strip() == "":
            return None
        try:
            parsed = phonenumbers.parse(value, None)
            if not phonenumbers.is_valid_number(parsed):
                raise PydanticCustomError("phone_number.invalid", "Invalid phone number format")
        except phonenumbers.NumberParseException:
            raise PydanticCustomError("phone_number.unparsable", "Invalid phone number format")
        return phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.E164)

    model_config = {"extra": "forbid"}


class ChangePasswordSchema(BaseModel):
    old_password: str
    new_password: Password
    confirm_new_password: Password

    @model_validator(mode="after")
    def check_passwords_match(self):
        if self.new_password != self.confirm_new_password:
            raise PydanticCustomError("password_mismatch", "Passwords do not match")
        return self

    @field_validator("new_password", "confirm_new_password")
    def validate_password(cls, value):
        if len(value) < 4:
            raise PydanticCustomError("password_too_short", "Password should have at least 4 characters")
        return value


class NameChangeRequestCreateSchema(BaseModel):
    firstname: str
    lastname: str
    middlename: str | None = None
    reason_change: str


class NameChangeRequestViewSchema(UCIMixinSchema, NameChangeRequestCreateSchema):
    user_id: int
    status: NameChangeRequestStatusEnum
    reason_rejecting: str | None

    model_config = {"from_attributes": True}


class NameChangeRequestUpdateByAdminSchema(BaseModel):
    action: Literal["approve", "reject"]
    reason_rejecting: str | None = None

    @model_validator(mode="after")
    def check_reason_rejecting(self):
        if self.action == "reject" and self.reason_rejecting is None:
            raise PydanticCustomError(
                "reason_rejecting required",
                "reason rejecting when the request is rejected is required to be filled in",
            )
        return self
