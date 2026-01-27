from enum import Enum

from sqlalchemy import Enum as SQLAEnum, String, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database.mixins import UCIMixin
from app.core.database.setup_db import Base


# Добавление новых типов через ручное написание миграции
class ContactMessageTypeEnum(str, Enum):
    CONTACT = "CONTACT"
    GET_INVOLVED = "GET_INVOLVED"
    GET_INVOLVED_COMMITTEES = "GET_INVOLVED_COMMITTEES"


class ContactMessage(Base, UCIMixin):
    __tablename__ = "contact_messages"

    # general fields
    name: Mapped[str] = mapped_column(String(256), nullable=False)
    email: Mapped[str] = mapped_column(String(256), nullable=False)
    type: Mapped[ContactMessageTypeEnum] = mapped_column(
        SQLAEnum(ContactMessageTypeEnum, name="contact_message_type_enum"),
        nullable=False,
    )
    answered: Mapped[bool] = mapped_column(default=False, server_default=text("false"))

    message_content: Mapped[dict] = mapped_column(JSONB(), nullable=False)
