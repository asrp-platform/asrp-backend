from pydantic import BaseModel, field_validator
from pydantic_core import PydanticCustomError


class FeedbackAdditionalInfoCreateSchema(BaseModel):
    hear_about_asrp: str
    tg_username: str | None
    interest_description: str | None

    model_config = {
        "from_attributes": True,
    }

    @field_validator("tg_username")
    def tg_username_validator(cls, v):
        if not v.startswith("@"):
            raise PydanticCustomError(
                "invalid_telegram_username",
                "Telegram username must start with '@'"
            )

        v = v[1:]
        if len(v) < 5 or len(v) > 32:
            raise PydanticCustomError(
                "invalid_telegram_username",
                "Telegram username must be at least 5 and less than 32 characters"
            )
        return v
