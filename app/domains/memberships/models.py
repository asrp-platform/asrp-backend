from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
from enum import Enum
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Enum as SQLAEnum, ForeignKey, Numeric, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database.mixins import UCIMixin
from app.core.database.setup_db import Base

if TYPE_CHECKING:
    from app.domains.users.models import User


class MembershipTypeEnum(Enum):
    ACTIVE = "ACTIVE"
    TRAINEE = "TRAINEE"
    AFFILIATE = "AFFILIATE"
    HONORARY = "HONORARY"
    PATHWAY = "PATHWAY"


class MembershipType(Base):
    __tablename__ = "membership_types"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    name: Mapped[str] = mapped_column(nullable=False)
    type: Mapped[MembershipTypeEnum] = mapped_column(
        SQLAEnum(MembershipTypeEnum, name="membership_type_enum"),
        nullable=False,
    )
    price_usd: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    duration: Mapped[int] = mapped_column(nullable=False, default=365)
    description: Mapped[str] = mapped_column(nullable=True)
    is_purchasable: Mapped[bool] = mapped_column(nullable=False, default=True, server_default=text("true"))

    user_memberships: Mapped[list["UserMembership"]] = relationship("UserMembership", back_populates="membership_type")


class ApprovalStatusEnum(Enum):
    APPROVED = "APPROVED"
    PENDING = "PENDING"
    REJECTED = "REJECTED"


class UserMembership(Base, UCIMixin):
    __tablename__ = "users_memberships"

    approval_status: Mapped[ApprovalStatusEnum] = mapped_column(
        SQLAEnum(ApprovalStatusEnum, name="approval_status_enum"),
        nullable=False,
        default=ApprovalStatusEnum.PENDING,
        server_default=text("'PENDING'"),
    )

    current_period_end: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    auto_renewal: Mapped[bool] = mapped_column(default=True, server_default=text("true"))

    primary_affiliation: Mapped[str] = mapped_column(nullable=False)
    job_title: Mapped[str] = mapped_column(nullable=False)
    practice_setting: Mapped[str] = mapped_column(nullable=False)
    subspecialty: Mapped[str] = mapped_column(nullable=False)
    is_trained_in_us: Mapped[bool] = mapped_column(nullable=False)

    @property
    def has_access(self) -> bool:
        if self.approval_status != ApprovalStatusEnum.APPROVED:
            return False
        if self.current_period_end is None:
            return True
        return self.current_period_end > datetime.now(tz=timezone.utc)

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), unique=True)
    user: Mapped["User"] = relationship("User", back_populates="memberships")

    membership_type_id: Mapped[int] = mapped_column(ForeignKey("membership_types.id"), nullable=False)
    membership_type: Mapped["MembershipType"] = relationship("MembershipType", back_populates="user_memberships")
