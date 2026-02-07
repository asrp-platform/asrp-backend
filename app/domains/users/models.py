from datetime import datetime
from typing import TYPE_CHECKING

from passlib.hash import bcrypt
from sqlalchemy import Boolean, DateTime, String, func, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database.setup_db import Base
from app.domains.memberships.models import UserMembership

if TYPE_CHECKING:
    from app.domains.news.models import News
    from app.domains.permissions.models import Permission


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True, nullable=False)
    firstname: Mapped[str] = mapped_column(nullable=False)
    middlename: Mapped[str] = mapped_column(nullable=True)
    lastname: Mapped[str] = mapped_column(nullable=False)
    suffix: Mapped[str] = mapped_column(nullable=True)
    credentials: Mapped[str] = mapped_column(nullable=True)
    email: Mapped[str] = mapped_column(unique=True, nullable=False, index=True)
    phone_number: Mapped[str] = mapped_column(String(20), nullable=True, unique=True)
    stuff: Mapped[bool] = mapped_column(Boolean(), default=False, nullable=False)
    description: Mapped[str] = mapped_column(String(512), nullable=True)
    country: Mapped[str] = mapped_column(nullable=False)
    state: Mapped[str] = mapped_column(nullable=True)
    city: Mapped[str] = mapped_column(nullable=False)
    languages_spoken: Mapped[str] = mapped_column(nullable=True)
    professional_interests: Mapped[str] = mapped_column(nullable=True)
    telegram_username: Mapped[str] = mapped_column(nullable=True, unique=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=func.now(), server_default=func.now(), nullable=False
    )
    pending: Mapped[bool] = mapped_column(default=True, nullable=True, server_default=text("true"))
    institution: Mapped[str] = mapped_column()
    role: Mapped[str] = mapped_column()

    last_password_change: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    email_confirmed: Mapped[bool] = mapped_column(default=False, server_default=text("false"))

    news: Mapped[list["News"]] = relationship("News", back_populates="author")
    memberships: Mapped[list["UserMembership"]] = relationship("UserMembership", back_populates="user")
    permissions: Mapped[list["Permission"]] = relationship(
        "Permission", back_populates="users", secondary="users_permissions"
    )

    _password: Mapped[str] = mapped_column()
    avatar_path: Mapped[str] = mapped_column(nullable=True, unique=True)

    @property
    def password(self) -> str:
        return self._password

    @password.setter
    def password(self, value: str) -> None:
        self._password = bcrypt.hash(value)

    def verify_password(self, plain_password: str) -> bool:
        return bcrypt.verify(plain_password, self._password)
