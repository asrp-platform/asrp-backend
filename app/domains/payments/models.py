import uuid
from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Enum as SQLAEnum, ForeignKey, Uuid, func, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database.setup_db import Base

if TYPE_CHECKING:
    from app.domains.users.models import User


class PaymentProvider(str, Enum):
    STRIPE = "STRIPE"


class PaymentStatusEnum(str, Enum):
    PENDING = "PENDING"
    SUCCEEDED = "SUCCEEDED"
    FAILED = "FAILED"
    CANCELED = "CANCELED"
    EXPIRED = "EXPIRED"
    REFUNDED = "REFUNDED"


class PaymentPurposeEnum(str, Enum):
    MEMBERSHIP_APPLICATION = "MEMBERSHIP_APPLICATION"
    MEMBERSHIP_RENEWAL = "MEMBERSHIP_RENEWAL"
    DONATION = "DONATION"


class Payment(Base):
    __tablename__ = "payments"

    provider: Mapped[PaymentProvider] = mapped_column(SQLAEnum(PaymentProvider, name="payment_provider_enum"))

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    amount: Mapped[Decimal] = mapped_column(nullable=False)
    currency: Mapped[str] = mapped_column(nullable=False, default="USD", server_default=text("'USD'"))

    # Internal payment status
    status: Mapped[PaymentStatusEnum] = mapped_column(
        SQLAEnum(PaymentStatusEnum, name="payment_status_enum"),
        nullable=False,
        default=PaymentStatusEnum.PENDING,
        server_default=text("'PENDING'"),
    )
    purpose: Mapped[PaymentPurposeEnum] = mapped_column(
        SQLAEnum(PaymentPurposeEnum, name="payment_purpose_enum"),
        nullable=False,
    )

    provider_data: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=func.now(), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=func.now(),
        onupdate=func.now(),
        server_default=func.now(),
        nullable=False,
    )

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=True)
    user: Mapped["User"] = relationship("User", back_populates="payments")


class ProcessedWebhookEvent(Base):
    __tablename__ = "processed_webhook_events"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    provider: Mapped[str] = mapped_column(nullable=False)
    event_id: Mapped[str] = mapped_column(nullable=False, unique=True)
    event_type: Mapped[str] = mapped_column(nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
