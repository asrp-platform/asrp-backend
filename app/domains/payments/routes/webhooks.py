import stripe
from fastapi import APIRouter, Header, HTTPException
from loguru import logger
from starlette.requests import Request

from app.core.config import settings
from app.core.logging import STRIPE_CHANNEL
from app.domains.payments.models import PaymentStatusEnum
from app.domains.payments.use_cases.process_async_payment_event import ProcessCheckoutSessionAsyncPaymentUseCaseDep
from app.domains.payments.use_cases.process_checkout_session_completed import ProcessCheckoutSessionCompletedUseCaseDep
from app.domains.payments.use_cases.process_payment_event import ProcessPaymentUseCaseDep

stripe.api_key = settings.STRIPE_API_KEY

stripe_logger = logger.bind(channel=STRIPE_CHANNEL)

router = APIRouter(prefix="/payments", tags=["Payments"])


@router.post("/stripe/webhook")
async def stripe_webhook(
    request: Request,
    process_payment_use_case: ProcessPaymentUseCaseDep,
    process_checkout_session_completed_use_case: ProcessCheckoutSessionCompletedUseCaseDep,
    process_checkout_session_async_payment_use_case: ProcessCheckoutSessionAsyncPaymentUseCaseDep,
    stripe_signature: str | None = Header(default=None, alias="Stripe-Signature"),
):
    payload = await request.body()

    if not stripe_signature:
        stripe_logger.warning("Stripe webhook rejected: Missing signature")
        raise HTTPException(status_code=400, detail="Missing Stripe-Signature header")
    try:
        event = stripe.Webhook.construct_event(
            payload=payload,
            sig_header=stripe_signature,
            secret=settings.STRIPE_WEBHOOK_SECRET,
        )
    except ValueError:
        stripe_logger.warning("Stripe webhook rejected: Invalid payload")
        raise HTTPException(status_code=400, detail="Invalid payload")
    except stripe.error.SignatureVerificationError:
        stripe_logger.warning("Stripe webhook rejected: Invalid signature")
        raise HTTPException(status_code=400, detail="Invalid signature")

    event_id = event["id"]
    event_type = event["type"]

    stripe_logger.info("Stripe webhook received: event_id={} event_type={}", event_id, event_type)
    if event_type == "payment_intent.succeeded":
        await process_payment_use_case.execute(event, target_payment_status=PaymentStatusEnum.SUCCEEDED)

    elif event_type == "payment_intent.payment_failed":
        # Тут обрабатываем неуспешную попытку оплаты
        await process_payment_use_case.execute(event, target_payment_status=PaymentStatusEnum.FAILED)

    elif event_type == "checkout.session.completed":
        # Если сессия умерла (пользователь забросил ее), то checkout.session.completed не будет
        await process_checkout_session_completed_use_case.execute(event)

    elif event_type in {"checkout.session.async_payment_succeeded", "checkout.session.async_payment_failed"}:
        await process_checkout_session_async_payment_use_case.execute(event)
    else:
        stripe_logger.info()
