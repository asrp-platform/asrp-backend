from decimal import Decimal

from fastapi import APIRouter
from pydantic import BaseModel, EmailStr, Field

from app.domains.payments.use_cases.make_donation import MakeDonationUseCaseDep
from app.domains.shared.schemas import PaymentCheckoutSchema


router = APIRouter(prefix="/payments/donations", tags=["Payments"])


class CreateDonationCheckoutSchema(BaseModel):
    amount_usd: Decimal = Field(
        ge=Decimal("1.00"),
        decimal_places=2,
    )
    customer_email: EmailStr


@router.post("", status_code=201, summary="Creates checkout session for a one-time donation")
async def create_one_time_donation(
    request_data: CreateDonationCheckoutSchema,
    use_case: MakeDonationUseCaseDep,
) -> PaymentCheckoutSchema:
    checkout_session_url = await use_case.execute(
        price_usd=request_data.amount_usd, customer_email=request_data.customer_email
    )

    return PaymentCheckoutSchema(checkout_session_url=checkout_session_url)
