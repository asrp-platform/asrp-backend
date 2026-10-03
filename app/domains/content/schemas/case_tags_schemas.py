from pydantic import BaseModel, ConfigDict, Field

from app.core.database.mixins import UCIMixinSchema


class CreateCaseTagSchema(BaseModel):
    name: str = Field(min_length=1, max_length=255)


class UpdateCaseTagSchema(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)


class CaseTagSchema(UCIMixinSchema):
    name: str

    model_config = ConfigDict(from_attributes=True)
