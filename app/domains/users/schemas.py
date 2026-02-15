import re
from datetime import datetime
from typing import Annotated, Optional

import phonenumbers
from pydantic import BaseModel, Field, field_validator, model_validator
from pydantic_core import PydanticCustomError

from app.core.database.mixins import UCIMixinSchema
from app.domains.shared.types import Password


class UserSchema(BaseModel):
    id: int
    firstname: str
    middlename: str | None
    lastname: str
    suffix: str | None
    credentials: str | None
    email: str
    stuff: bool
    description: str | None
    country: str
    state: str | None
    city: str
    languages_spoken: str | None
    professional_interests: str | None
    telegram_username: str | None
    created_at: datetime
    institution: str
    role: str
    avatar_path: str | None
    phone_number: str | None
    pending: bool
    last_password_change: datetime | None
    email_confirmed: bool

    model_config = {
        "from_attributes": True,
    }


class UpdateUserByAdminSchema(BaseModel):
    stuff: Optional[bool] = Field(None, description="Grant or revoke admin role for user")


class UpdateUserSchema(BaseModel):
    firstname: Annotated[str | None, Field(min_length=2)] = None
    middlename: str | None = None
    lastname: Annotated[str | None, Field(min_length=2)] = None
    suffix: str | None = None
    credentials: str | None = None
    description: str | None = None
    country: str | None = Field(None, min_length=2)
    state: str | None = None
    city: str | None = Field(None, min_length=2)
    languages_spoken: str | None = None
    professional_interests: str | None = None
    telegram_username: str | None = None
    institution: Annotated[str | None, Field(min_length=2)] = None
    role: str | None = None
    phone_number: Annotated[str | None, Field()] = None

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


class ChangePasswordSchema(BaseModel):
    old_password: str
    new_password: Password
    confirm_new_password: Password

    @model_validator(mode="after")
    def check_passwords_match(self):
        if self.new_password != self.confirm_new_password:
            raise PydanticCustomError(
                "password_mismatch",  # internal code
                "Passwords do not match",  # user-facing message
            )
        return self

    @field_validator("new_password", "confirm_new_password")
    def validate_password(cls, v):
        if len(v) < 4:
            raise PydanticCustomError("password_too_short", "Password should have at least 4 characters")
        return v


class PostgraduateTrainingMixin(BaseModel):
    institution: str = Field(min_length=2)
    speciality: str = Field(min_length=2)
    city: str = Field(min_length=2)
    state: str = Field(min_length=2)
    country: str = Field(min_length=2)
    years_from_to: str = Field(min_length=9, max_length=9)

    @field_validator("years_from_to")
    def validate_year_range(cls, value: str) -> str:
        YEAR_RANGE_REGEX = re.compile(r"^\d{4}-\d{4}$")
        if not YEAR_RANGE_REGEX.match(value):
            raise PydanticCustomError("year_range_error", "Format must be YYYY-YYYY")

        start, end = map(int, value.split("-"))

        if start > end:
            raise PydanticCustomError("year_range_error", "Start year cannot be greater than end year")

        if start < 1900 or end > 2100:
            raise PydanticCustomError("year_range_error", "Year out of valid range")

        return value


class ViewMixin(UCIMixinSchema):
    user_id: int


class ProfessionalInformationCreateOrUpdateSchema(BaseModel):
    medical_school: str
    medical_school_country: str
    years_from_to: str

    is_board_certified_pathologist: bool = False
    is_us_pathology_trainee: bool = False
    is_us_lab_professional: bool = False


class ProfessionalInformationViewSchema(ViewMixin, ProfessionalInformationCreateOrUpdateSchema):
    model_config = {
        "from_attributes": True,
    }


class ResidencyCreateSchema(PostgraduateTrainingMixin):
    pass


class ResidencyUpdateSchema(ResidencyCreateSchema):
    pass


class ResidencyViewSchema(ViewMixin, ResidencyCreateSchema):
    model_config = {
        "from_attributes": True,
    }


class FellowshipCreateSchema(PostgraduateTrainingMixin):
    pass


class FellowshipUpdateSchema(FellowshipCreateSchema):
    pass


class FellowshipViewSchema(ViewMixin, FellowshipCreateSchema):
    model_config = {
        "from_attributes": True,
    }
