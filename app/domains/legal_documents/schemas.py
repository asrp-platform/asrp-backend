from pydantic import BaseModel

from app.core.database.mixins import UCIMixinSchema


class ViewLegalDocumentSchema(BaseModel):
    url: str


class CreateSponsorSchema(BaseModel):
    name: str
    link: str
    short_name: str | None = None
    logo_url: str | None = None


class SponsorSchema(CreateSponsorSchema, UCIMixinSchema):
    model_config = {"from_attributes": True}


class UpdateSponsorSchema(BaseModel):
    name: str | None = None
    link: str | None = None
    short_name: str | None = None
    logo_url: str | None = None
