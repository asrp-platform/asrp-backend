import uuid
from datetime import datetime
from decimal import Decimal
from typing import Any

from pydantic import BaseModel, EmailStr, Field

from app.domains.payments.models import (
    PaymentProvider,
    PaymentPurposeEnum,
    PaymentStatusEnum,
)


class PaymentCheckoutSchema(BaseModel):
    checkout_session_url: str


class CreateDonationCheckoutSchema(BaseModel):
    amount_usd: Decimal = Field(ge=Decimal("1.00"), decimal_places=2)
    customer_email: EmailStr


class PaymentBaseSchema(BaseModel):
    provider: PaymentProvider
    amount: Decimal
    currency: str = "USD"
    status: PaymentStatusEnum = PaymentStatusEnum.PENDING
    purpose: PaymentPurposeEnum
    provider_data: dict[str, Any] | None = None
    user_id: int | None = None


class PaymentCreateSchema(BaseModel):
    provider: PaymentProvider
    amount: Decimal
    currency: str = "USD"
    purpose: PaymentPurposeEnum
    provider_data: dict[str, Any] | None = None
    user_id: int | None = None


class PaymentUpdateSchema(BaseModel):
    provider: PaymentProvider | None = None
    amount: Decimal | None = None
    currency: str | None = None
    status: PaymentStatusEnum | None = None
    purpose: PaymentPurposeEnum | None = None
    provider_data: dict[str, Any] | None = None
    user_id: int | None = None


class PaymentReadSchema(PaymentBaseSchema):
    id: uuid.UUID
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
