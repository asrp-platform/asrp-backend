from typing import Literal

from pydantic import BaseModel

from app.core.database.mixins import UCIMixinSchema


class HeadingSchema(BaseModel):
    id: str
    type: Literal["heading"]
    level: Literal[1, 2, 3, 4, 5]
    text: str


class ListItemSchema(BaseModel):
    id: str
    text: str


class ListSchema(BaseModel):
    id: str
    type: Literal["list"]
    items: list[ListItemSchema]


class ParagraphSchema(BaseModel):
    id: str
    type: Literal["paragraph"]
    text: str


class ContentSchema(BaseModel):
    blocks: list[HeadingSchema | ListSchema | ParagraphSchema]


class CreateBoardMemberSchema(BaseModel):
    role: str
    name: str
    photo_url: str | None = None
    order: int | None = None
    is_visible: bool | None = None
    content: dict


class UpdateBoardMemberSchema(BaseModel):
    role: str | None = None
    name: str | None = None
    photo_url: str | None = None
    is_visible: bool | None = None

    content: dict | None = None


class BoardMemberSchema(CreateBoardMemberSchema, UCIMixinSchema):
    model_config = {"from_attributes": True}


class CardOrderUpdate(BaseModel):
    id: int
    order: int
