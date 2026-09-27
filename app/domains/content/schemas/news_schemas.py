from pydantic import BaseModel, ConfigDict

from app.core.database.mixins import UCIMixinSchema
from app.domains.users.schemas import UserPublicSchema


class CreateNewsSchema(BaseModel):
    title: str
    cover_key: str | None
    body: dict
    when: str | None
    where: str | None
    is_published: bool


class UpdateNewsSchema(BaseModel):
    title: str | None = None
    cover_key: str | None = None
    body: dict | None = None
    when: str | None = None
    where: str | None = None
    is_published: bool | None = None


class NewsSchema(CreateNewsSchema, UCIMixinSchema):
    slug: str
    author_id: int
    cover_url: str | None = None

    model_config = ConfigDict(from_attributes=True)


class NewsWithAuthorSchema(NewsSchema):
    author: UserPublicSchema
