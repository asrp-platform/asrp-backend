from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database.mixins import UCIMixin
from app.core.database.setup_db import Base


class DirectorBoardMember(Base, UCIMixin):
    __tablename__ = "directors_board_members"

    role: Mapped[str] = mapped_column(nullable=False)
    name: Mapped[str] = mapped_column(nullable=False)
    photo_url: Mapped[str] = mapped_column(nullable=True)

    content: Mapped[dict] = mapped_column(JSONB, nullable=False)
    order: Mapped[int] = mapped_column(nullable=False, unique=True)
    is_visible: Mapped[bool] = mapped_column(nullable=False, default=True)
