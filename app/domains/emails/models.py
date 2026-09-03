from enum import Enum
from typing import TYPE_CHECKING

from sqlalchemy import Enum as SQLAEnum, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database.mixins import UCIMixin
from app.core.database.setup_db import Base


if TYPE_CHECKING:
    from app.domains.users.models import User


class EmailTemplateTypeEnum(str, Enum):
    CUSTOM = "custom"

    EMAIL_VERIFICATION = "email_verification"
    PASSWORD_RESET = "password_reset"

    MEMBERSHIP_RENEWAL = "membership_renewal"
    MEMBERSHIP_APPLICATION_RECEIVED = "membership_application_received"
    MEMBERSHIP_APPLICATION_APPROVED = "membership_application_approved"
    MEMBERSHIP_APPLICATION_REJECTED = "membership_application_rejected"
    MEMBERSHIP_SUSPENDED = "membership_suspended"
    MEMBERSHIP_TERMINATED = "membership_terminated"


class EmailTemplate(Base, UCIMixin):
    __tablename__ = 'email_templates'

    name: Mapped[str] = mapped_column(nullable=False)
    subject: Mapped[str] = mapped_column(nullable=False)
    description: Mapped[str] = mapped_column(nullable=False)

    created_by_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=True)
    created_by: Mapped["User"] = relationship(
        back_populates="created_email_templates",
        foreign_keys=[created_by_id],
    )

    updated_by_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=True)
    updated_by: Mapped["User"] = relationship(
        back_populates="updated_email_templates",
        foreign_keys=[updated_by_id],
    )

    template_type: Mapped[EmailTemplateTypeEnum] = mapped_column(
        SQLAEnum(EmailTemplateTypeEnum, name="email_template_type_enum"),
        default=EmailTemplateTypeEnum.CUSTOM,
        nullable=False,
    )

    editor_state: Mapped[dict] = mapped_column(JSONB, nullable=False)
    html: Mapped[str] = mapped_column(nullable=False)
