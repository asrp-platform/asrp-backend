from decimal import ROUND_HALF_UP, Decimal

import stripe
from stripe.checkout import Session

from app.core.config import settings

stripe.api_key = settings.STRIPE_API_KEY


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


def to_stripe_amount(amount: Decimal, currency: str = "usd") -> int:
    currency = currency.lower()
    if currency == "usd":
        return int((amount * Decimal("100")).quantize(Decimal("1"), rounding=ROUND_HALF_UP))

    raise ValueError(f"Unsupported currency: {currency}")
