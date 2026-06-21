from datetime import datetime
from typing import TYPE_CHECKING

from pydantic import BaseModel
from sqlalchemy import ForeignKey, text
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database.mixins import UCIMixin
from app.core.database.setup_db import Base


if TYPE_CHECKING:
    from app.domains.users.models import User


class News(Base, UCIMixin):
    __tablename__ = "news"

    body: Mapped[str] = mapped_column(JSON(), nullable=False)

    is_published: Mapped[bool] = mapped_column(default=True, server_default=text("true"))

    author_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    author: Mapped["User"] = relationship("User", back_populates="news")

    is_deleted: Mapped[bool] = mapped_column(default=False, server_default=text("false"))


class CreateNewsSchema(BaseModel):
    body: dict

    model_config = {"from_attributes": True}


class UpdateNewsSchema(CreateNewsSchema):
    is_published: bool = True
    is_deleted: bool = False


class NewsSchema(UpdateNewsSchema):
    id: int
    author_id: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True, "protected_namespaces": ()}
