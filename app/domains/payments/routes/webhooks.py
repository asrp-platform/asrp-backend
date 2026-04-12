import stripe
from fastapi import APIRouter, Header, HTTPException
from starlette.requests import Request

from app.core.config import settings
from app.domains.payments.models import PaymentStatusEnum
from app.domains.payments.use_cases.process_payment_event import ProcessPaymentUseCaseDep

stripe.api_key = settings.STRIPE_API_KEY


router = APIRouter(prefix="/payments", tags=["Payments"])


@router.post("/stripe/webhook")
async def stripe_webhook(
    request: Request,
    process_payment_use_case: ProcessPaymentUseCaseDep,
    stripe_signature: str | None = Header(default=None, alias="Stripe-Signature"),
):
    payload = await request.body()

    if not stripe_signature:
        raise HTTPException(status_code=400, detail="Missing Stripe-Signature header")

    try:
        event = stripe.Webhook.construct_event(
            payload=payload,
            sig_header=stripe_signature,
            secret=settings.STRIPE_WEBHOOK_SECRET,
        )
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid payload")
    except stripe.error.SignatureVerificationError:
        raise HTTPException(status_code=400, detail="Invalid signature")

    event_type = event["type"]

    if event_type == "payment_intent.succeeded":
        await process_payment_use_case.execute(event, payment_status=PaymentStatusEnum.SUCCEEDED)

    elif event_type == "checkout.session.async_payment_succeeded":
        pass

    elif event_type == "payment_intent.payment_failed":
        # Тут обрабатываем неуспешную попытку оплаты
        await process_payment_use_case.execute(event, payment_status=PaymentStatusEnum.FAILED)

    elif event_type == "checkout.session.async_payment_failed" or event_type == "checkout.session.completed":
        pass
        # Здесь выдаем membership (продукт)
        # session = data_object
