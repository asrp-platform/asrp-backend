from datetime import date

from pydantic import BaseModel, ConfigDict, Field

from app.core.database.mixins import UCIMixinSchema
from app.domains.content.schemas.case_tags_schemas import CaseTagSchema


class CreateCaseOfTheMonthSchema(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    cover_key: str | None = None
    history: dict
    case_findings: dict
    virtual_slides: list[str] = Field(default_factory=list)
    questions: list[str] = Field(default_factory=list)
    publication_month: date
    answer: dict
    tag_ids: list[int] = Field(default_factory=list)


class UpdateCaseOfTheMonthSchema(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=255)
    cover_key: str | None = None
    history: dict | None = None
    case_findings: dict | None = None
    virtual_slides: list[str] | None = None
    questions: list[str] | None = None
    publication_month: date | None = None
    answer: dict | None = None
    tag_ids: list[int] | None = None


class CaseOfTheMonthSchema(UCIMixinSchema):
    title: str
    slug: str
    cover_key: str | None
    cover_url: str | None = None
    history: dict
    case_findings: dict
    virtual_slides: list[str]
    questions: list[str]
    publication_month: date
    answer: dict
    tags: list[CaseTagSchema]

    model_config = ConfigDict(from_attributes=True)
