from pydantic import BaseModel, field_validator
from pydantic_core import PydanticCustomError


class FeedbackAdditionalInfoCreateSchema(BaseModel):
    hear_about_asrp: str
    tg_username: str | None = None
    interest_description: str | None = None

    model_config = {
        "from_attributes": True,
    }

    @field_validator("tg_username")
    def tg_username_validator(cls, v):
        if v is None:
            return v

        v = v.strip()

        if not v:
            return None

        if not v.startswith("@"):
            raise PydanticCustomError("invalid_telegram_username", "Telegram username must start with '@'")

        username = v[1:]

        if len(username) < 5 or len(username) > 32:
            raise PydanticCustomError(
                "invalid_telegram_username", "Telegram username must be at least 5 and less than 32 characters"
            )

        return username


class UploadedImageSchema(BaseModel):
    path: str
