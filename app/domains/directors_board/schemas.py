from pydantic import BaseModel

from app.core.database.mixins import UCIMixinSchema


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
