from datetime import datetime, timedelta
from typing import TYPE_CHECKING
from uuid import uuid4

from slugify import slugify
from sqlalchemy import DateTime, ForeignKey, String, Text, event, text
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


class Webinar(Base, UCIMixin):
    __tablename__ = "webinars"

    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    learning_objectives: Mapped[list[str]] = mapped_column(
        JSON,
        nullable=False,
        default=list,
    )
    slug: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        unique=True,
        index=True,
    )

    speaker_name: Mapped[str] = mapped_column(nullable=False)
    speaker_description: Mapped[str] = mapped_column(nullable=True)

    join_link: Mapped[str | None] = mapped_column(Text, nullable=True)
    bunny_video_id: Mapped[str | None] = mapped_column(String, nullable=True)

    starts_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    ends_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    location: Mapped[str | None] = mapped_column(String(255), nullable=True)
    timezone: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        default="America/Chicago",
        server_default="America/Chicago",
    )

    member_only: Mapped[bool] = mapped_column(nullable=False, default=True, server_default=text("true"))

    archived: Mapped[bool] = mapped_column(nullable=False, default=False, server_default=text("false"))
    language: Mapped[str] = mapped_column(nullable=True)

    registered_users: Mapped[list["User"]] = relationship(
        "User",
        back_populates="webinars",
        secondary="webinars_registered_users",
    )


class WebinarRegisteredUsers(Base):
    __tablename__ = "webinars_registered_users"

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), primary_key=True, nullable=False)
    webinar_id: Mapped[int] = mapped_column(ForeignKey("webinars.id"), primary_key=True, nullable=False)


@event.listens_for(Webinar, "before_insert")
def generate_webinar_slug(mapper, connection, target: Webinar) -> None:  # noqa SQLAlchemy event function parameters
    if not target.slug:
        title_slug = (
            slugify(
                target.title,
                max_length=246,
                word_boundary=True,
                save_order=True,
            )
            or "webinar"
        )

        target.slug = f"{title_slug}-{uuid4().hex[:8]}"


@event.listens_for(Webinar, "before_insert")
def set_ends_at(mapper, connection, target: Webinar) -> None:  # noqa SQLAlchemy event function parameters
    if not target.ends_at:
        ends_at = target.starts_at + timedelta(hours=2)
        target.ends_at = ends_at
