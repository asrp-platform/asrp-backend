from __future__ import annotations

from datetime import datetime
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

    membership_requests: Mapped[list["MembershipRequest"]] = relationship(
        "MembershipRequest", back_populates="membership_type"
    )


class MembershipRequestStatusEnum(str, Enum):
    PAYMENT_PENDING = "PAYMENT_PENDING"
    PAID = "PAID"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    PAYMENT_FAILED = "PAYMENT_FAILED"


class MembershipRequest(Base, UCIMixin):
    __tablename__ = "membership_requests"

    status: Mapped[MembershipRequestStatusEnum] = mapped_column(
        SQLAEnum(MembershipRequestStatusEnum, name="membership_request_status_enum"),
        nullable=False,
        default=MembershipRequestStatusEnum.PAYMENT_PENDING,
        server_default=text("'PAYMENT_PENDING'"),
    )

    primary_affiliation: Mapped[str] = mapped_column(nullable=False)
    job_title: Mapped[str] = mapped_column(nullable=False)
    practice_setting: Mapped[str] = mapped_column(nullable=False)
    subspecialty: Mapped[str] = mapped_column(nullable=False)

    reviewed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    admin_comment: Mapped[str | None] = mapped_column(nullable=True)

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), unique=True)
    user: Mapped["User"] = relationship("User", back_populates="membership_request")

    membership_type_id: Mapped[int] = mapped_column(ForeignKey("membership_types.id"), nullable=False)
    membership_type: Mapped["MembershipType"] = relationship("MembershipType", back_populates="membership_requests")
