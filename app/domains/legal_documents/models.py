from sqlalchemy.orm import Mapped, mapped_column

from app.core.database.mixins import UCIMixin
from app.core.database.setup_db import Base


class Sponsor(Base, UCIMixin):
    __tablename__ = "sponsors"

    name: Mapped[str] = mapped_column(nullable=False)
    short_name: Mapped[str] = mapped_column(nullable=True)
    logo_key: Mapped[str] = mapped_column(nullable=True)
    link: Mapped[str] = mapped_column(nullable=False)
