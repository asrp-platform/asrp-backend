from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database.mixins import UCIMixin
from app.core.database.setup_db import Base


class EmailTemplate(Base, UCIMixin):
    __tablename__ = 'email_templates'

    name: Mapped[str] = mapped_column(nullable=False)
    subject: Mapped[str] = mapped_column(nullable=False)
    description: Mapped[str] = mapped_column(nullable=True)

    editor_state: Mapped[dict] = mapped_column(JSONB, nullable=False)
    html: Mapped[str] = mapped_column(nullable=False)
