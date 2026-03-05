from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING, Optional

from pydantic import BaseModel, Field
from sqlalchemy import DateTime, Enum as SQLAEnum, ForeignKey, Numeric, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database.mixins import UCIMixin
from app.core.database.setup_db import Base
from app.domains.memberships.enums import ApprovalStatusEnum, MembershipTypeEnum

if TYPE_CHECKING:
    from app.domains.users.models import User, UserSchema


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

    memberships: Mapped[list["UserMembership"]] = relationship("UserMembership", back_populates="membership_type")


class UserMembership(Base, UCIMixin):
    __tablename__ = "users_memberships"

    approval_status: Mapped[ApprovalStatusEnum] = mapped_column(
        SQLAEnum(ApprovalStatusEnum, name="approval_status_enum"),
        nullable=False,
        default=ApprovalStatusEnum.PENDING,
        server_default=text("'PENDING'"),
    )

    current_period_end: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    cancel_at_period_end: Mapped[bool] = mapped_column(default=False, server_default=text("false"))

    primary_affiliation: Mapped[str] = mapped_column(nullable=False)
    job_title: Mapped[str] = mapped_column(nullable=False)
    practice_setting: Mapped[str] = mapped_column(nullable=False)
    subspecialty: Mapped[str] = mapped_column(nullable=False)
    is_trained_in_us: Mapped[bool] = mapped_column(nullable=False)

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), unique=True)
    user: Mapped["User"] = relationship("User", back_populates="membership")

    membership_type_id: Mapped[int] = mapped_column(ForeignKey("membership_types.id"), nullable=False)
    membership_type: Mapped["MembershipType"] = relationship("MembershipType", back_populates="memberships")


class UpdateMembershipTypeSchema(BaseModel):
    type: Optional[MembershipTypeEnum] = Field(None)
    description: Optional[str] = Field(None)
    is_purchasable: Optional[bool] = Field(None)
    price_usd: Optional[float] = Field(None)


class MembershipTypeSchema(BaseModel):
    id: int
    name: str
    type: MembershipTypeEnum
    price_usd: float
    duration: int
    description: str
    is_purchasable: bool

    model_config = {
        "from_attributes": True,
    }


class UpdateUserMembershipSchema(BaseModel):
    approval_status: ApprovalStatusEnum = Field(None)


class UserMembershipSchema(BaseModel):
    id: int

    created_at: datetime
    updated_at: datetime

    approval_status: ApprovalStatusEnum

    current_period_end: datetime | None
    cancel_at_period_end: bool

    has_access: bool

    user_id: int
    membership_type_id: int

    model_config = {
        "from_attributes": True,
    }


class ExtendedUserMembershipSchema(UserMembershipSchema):
    user: UserSchema
    membership_type: MembershipTypeSchema

    model_config = {
        "from_attributes": True,
    }
