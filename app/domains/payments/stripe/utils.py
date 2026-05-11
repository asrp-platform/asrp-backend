from decimal import ROUND_HALF_UP, Decimal

import stripe
from loguru import logger
from stripe.checkout import Session

from app.core.config import settings
from app.core.logging import PAYMENTS_CHANNEL
from app.domains.payments.models import Payment

stripe.api_key = settings.STRIPE_API_KEY

payments_logger = logger.bind(channel=PAYMENTS_CHANNEL)


async def create_checkout_session(
    line_items: list[dict],
    metadata: dict = None,
    *,
    success_url: str,
    mode: str = "payment",
) -> Session:
    metadata = metadata or {}
    session = stripe.checkout.Session.create(
        mode=mode,
        success_url=success_url,
        line_items=line_items,
        metadata=metadata,
        payment_intent_data={"metadata": metadata},
    )
    return session


def create_stripe_refund(
    payment: Payment,
    idempotency_key: str,
):
    payment_intent_id = payment.provider_data.get("payment_intent_id")
    if not payment_intent_id:
        raise ValueError("Payment does not have Stripe payment_intent_id")

    try:
        refund = stripe.Refund.create(
            payment_intent=payment_intent_id,
            reason="requested_by_customer",
            metadata={
                "payment_id": str(payment.id),
                "membership_request_id": str(payment.membership_request_id),
                "purpose": payment.purpose.value,
            },
            idempotency_key=idempotency_key,
        )
        return refund
    except stripe.error.APIConnectionError:
        payments_logger.exception(
            "Stripe refund network error: payment_id={} payment_intent_id={} idempotency_key={}",
            payment.id,
            payment_intent_id,
            idempotency_key,
        )
        raise
    except stripe.error.StripeError:
        payments_logger.exception(
            "Stripe refund API error: payment_id={} payment_intent_id={} idempotency_key={}",
            payment.id,
            payment_intent_id,
            idempotency_key,
        )
        raise


def to_stripe_amount(amount: Decimal, currency: str = "usd") -> int:
    currency = currency.lower()
    if currency == "usd":
        return int((amount * Decimal("100")).quantize(Decimal("1"), rounding=ROUND_HALF_UP))

    raise ValueError(f"Unsupported currency: {currency}")
