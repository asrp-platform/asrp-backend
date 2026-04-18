from decimal import ROUND_HALF_UP, Decimal

import stripe
from stripe.checkout import Session

from app.core.config import settings

stripe.api_key = settings.STRIPE_API_KEY


async def create_checkout_session(
    line_items: list[dict],
    # success_url: str,
    mode: str = "payment",
) -> Session:
    session = stripe.checkout.Session.create(
        mode=mode,
        success_url="https://example.com/success",
        line_items=line_items,
    )
    return session


def to_stripe_amount(amount: Decimal, currency: str = "usd") -> int:
    currency = currency.lower()

    # Для твоего текущего кейса USD
    if currency == "usd":
        return int((amount * Decimal("100")).quantize(Decimal("1"), rounding=ROUND_HALF_UP))

    raise ValueError(f"Unsupported currency: {currency}")
