from pydantic import BaseModel, EmailStr, Field, field_validator, model_validator
from pydantic_core import PydanticCustomError

from app.domains.shared.types import Password


class RegisterFormData(BaseModel):
    email: EmailStr = Field(min_length=6)
    password: str = Password
    repeat_password: Password
    firstname: str = Field(min_length=2)
    lastname: str = Field(min_length=2)
    country: str = Field(min_length=2)
    city: str = Field(min_length=2)
    institution: str = Field(min_length=2)
    role: str = Field(min_length=2)

    @model_validator(mode="after")
    def check_passwords_match(self):
        if self.password != self.repeat_password:
            raise ValueError("Passwords do not match")
        return self


class LoginForm(BaseModel):
    email: str
    password: str
    remember: bool = False

    class Config:
        json_schema_extra = {"examples": [{"email": "admin@mail.com", "password": "admin", "remember": True}]}


class AccessToken(BaseModel):
    access_token: str
    type: str = "Bearer"


class JWTTokenResponse(AccessToken):
    refresh_token: str | None


class ResetPasswordSchema(BaseModel):
    email: EmailStr


class ChangePasswordSchema(BaseModel):
    password: Password
    confirm_password: Password

    @model_validator(mode="after")
    def check_passwords_match(self):
        if self.password != self.confirm_password:
            raise PydanticCustomError(
                "password_mismatch",  # internal code
                "Passwords do not match",  # user-facing message
            )
        return self

    @field_validator("password", "confirm_password")
    def validate_password(cls, v):
        if len(v) < 4:
            raise PydanticCustomError("password_too_short", "Password should have at least 4 characters")
        return v
