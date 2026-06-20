from typing import TYPE_CHECKING

from pydantic import BaseModel
from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database.setup_db import Base


if TYPE_CHECKING:
    from app.domains.users.models import User


class Permission(Base):
    __tablename__ = "permissions"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    action: Mapped[str] = mapped_column(nullable=False)
    users: Mapped[list["User"]] = relationship(
        "User",
        back_populates="permissions",
        secondary="users_permissions",
    )
    name: Mapped[str] = mapped_column(nullable=False)


class UserPermission(Base):
    __tablename__ = "users_permissions"

    permission_id: Mapped[int] = mapped_column(ForeignKey("permissions.id"), primary_key=True)
    user_id: Mapped[id] = mapped_column(ForeignKey("users.id"), primary_key=True)


class PermissionSchema(BaseModel):
    id: int
    action: str
    name: str

    model_config = {"from_attributes": True}
