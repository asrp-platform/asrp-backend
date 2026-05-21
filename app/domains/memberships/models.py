from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
from enum import Enum
from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, DateTime, Enum as SQLAEnum, ForeignKey, Index, Numeric, String, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database.mixins import UCIMixin
from app.core.database.setup_db import Base
from app.domains.payments.models import Payment

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
    user_membership: Mapped[list["UserMembership"]] = relationship("UserMembership", back_populates="membership_type")


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

    reviewer_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=True)
    reviewer: Mapped["User"] = relationship(
        "User", back_populates="reviewed_membership_request", foreign_keys=[reviewer_id]
    )

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), unique=True)
    user: Mapped["User"] = relationship("User", back_populates="membership_request", foreign_keys=[user_id])

    membership_type_id: Mapped[int] = mapped_column(ForeignKey("membership_types.id"), nullable=False)
    membership_type: Mapped["MembershipType"] = relationship("MembershipType", back_populates="membership_requests")

    user_membership: Mapped["UserMembership"] = relationship("UserMembership", back_populates="membership_request")
    payments: Mapped[list[Payment]] = relationship("Payment", back_populates="membership_request", uselist=True)


class UserMembership(Base, UCIMixin):
    __tablename__ = "users_memberships"

    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, unique=True)
    user: Mapped["User"] = relationship("User", back_populates="membership")

    membership_request_id: Mapped[int] = mapped_column(
        ForeignKey("membership_requests.id"), nullable=False, unique=True
    )
    membership_request: Mapped["MembershipRequest"] = relationship(
        "MembershipRequest", back_populates="user_membership"
    )

    membership_type_id: Mapped[int] = mapped_column(ForeignKey("membership_types.id"), nullable=False)
    membership_type: Mapped["MembershipType"] = relationship("MembershipType", back_populates="user_membership")

    @property
    def is_active(self) -> bool:
        return datetime.now(timezone.utc) < self.expires_at


class UserMembershipTypeChangeRequests(Base, UCIMixin):
    __tablename__ = "user_membership_type_change_requests"

    target_membership_type_id: Mapped[int] = mapped_column(ForeignKey("membership_types.id"), nullable=False)
    target_membership_type = relationship("MembershipType")

    user_membership_id: Mapped[int] = mapped_column(ForeignKey("users_memberships.id"), nullable=False)

    upgrade: Mapped[bool] = mapped_column(nullable=False)  # in upgrade is False it means downgrade
    reason_changing: Mapped[str | None] = mapped_column(String(512), nullable=False)

    approved: Mapped[bool] = mapped_column(default=False, server_default=text("false"), nullable=False)
    admin_comment: Mapped[str | None] = mapped_column(nullable=True)

    pending: Mapped[bool] = mapped_column(default=True, server_default=text("true"), nullable=False)

    __table_args__ = (
        CheckConstraint("approved = TRUE or admin_comment IS NOT NULL"),
        Index(
            "unique_pending_membership_type_change_request_per_user_membership",
            "user_membership_id",
            unique=True,
            postgresql_where=(pending is True),
        ),
    )
