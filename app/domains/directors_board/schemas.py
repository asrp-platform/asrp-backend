from typing import Literal

from pydantic import BaseModel

from app.core.database.mixins import UCIMixinSchema


class HeadingSchema(BaseModel):
    type: Literal["heading"]
    level: Literal[1, 2, 3, 4, 5]
    text: str


class ListSchema(BaseModel):
    type: Literal["list"]
    items: list[str]


class ParagraphSchema(BaseModel):
    type: Literal["paragraph"]
    text: str


class ContentSchema(BaseModel):
    blocks: list[HeadingSchema | ListSchema | ParagraphSchema]


class CreateBoardMemberSchema(BaseModel):
    role: str
    name: str
    photo_url: str

    content: ContentSchema
    order: int
    is_visible: bool


class BoardMemberSchema(CreateBoardMemberSchema, UCIMixinSchema):
    model_config = {"from_attributes": True}
