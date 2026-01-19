from datetime import datetime
from enum import Enum
from typing import Annotated

from pydantic import BaseModel, EmailStr, Field
from sqlalchemy import Enum as SQLAEnum, String, Text, text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database.mixins import UCIMixin
from app.core.database.setup_db import Base


# Добавление новых типов через ручное написание миграции
class ContactMessageTypeEnum(str, Enum):
    CONTACT_MESSAGE = "CONTACT_MESSAGE"
    GET_INVOLVED_MESSAGE = "GET_INVOLVED_MESSAGE"


class ContactMessage(Base, UCIMixin):
    __tablename__ = "contact_messages"

    # general fields
    name: Mapped[str] = mapped_column(String(256), nullable=False)
    email: Mapped[str] = mapped_column(String(256), nullable=False)

    # contact message type fields
    subject: Mapped[str] = mapped_column(String(256), nullable=True)
    contact_message: Mapped[str] = mapped_column(Text(), nullable=True)

    # get involved fields
    role_affiliation: Mapped[str] = mapped_column(String(256), nullable=True)
    get_involved_message: Mapped[str] = mapped_column(Text(), nullable=True)

    type: Mapped[ContactMessageTypeEnum] = mapped_column(
        SQLAEnum(ContactMessageTypeEnum, name="contact_message_type_enum"),
        nullable=False,
    )

    answered: Mapped[bool] = mapped_column(default=False, server_default=text("false"))


class BaseMessageSchema(BaseModel):
    name: str = Field(min_length=2, max_length=256)
    email: EmailStr
    type: ContactMessageTypeEnum


class CreateContactMessageSchema(BaseMessageSchema):
    subject: Annotated[str | None, Field(min_length=2)] = None
    contact_message: Annotated[str | None, Field(min_length=10)] = None
    role_affiliation: Annotated[str | None, Field(min_length=2)] = None
    get_involved_message: Annotated[str | None, Field(min_length=10)] = None


class ContactMessageResponseSchema(CreateContactMessageSchema):
    id: int
    created_at: datetime
    updated_at: datetime
    answered: bool

    model_config = {
        "from_attributes": True,
    }
