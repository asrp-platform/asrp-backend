from fastapi import APIRouter

from app.domains.payments.schemas import CreateDonationCheckoutSchema, PaymentCheckoutSchema
from app.domains.payments.use_cases.make_donation import MakeDonationUseCaseDep


router = APIRouter(prefix="/payments/donations", tags=["Payments"])


@router.post("", status_code=201, summary="Creates checkout session for a one-time donation")
async def create_one_time_donation(
    request_data: CreateDonationCheckoutSchema,
    use_case: MakeDonationUseCaseDep,
) -> PaymentCheckoutSchema:
    checkout_session_url = await use_case.execute(
        price_usd=request_data.amount_usd, customer_email=request_data.customer_email
    )

    return PaymentCheckoutSchema(checkout_session_url=checkout_session_url)
