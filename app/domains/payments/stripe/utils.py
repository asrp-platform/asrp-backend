from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal
from typing import TYPE_CHECKING

import stripe
from loguru import logger
from stripe.checkout import Session

from app.core.config import settings
from app.core.logging import PAYMENTS_CHANNEL
from app.domains.payments.models import Payment, PaymentPurposeEnum


if TYPE_CHECKING:
    from app.domains.memberships.models import MembershipRequest, MembershipType, UserMembership

stripe.api_key = settings.STRIPE_API_KEY

payments_logger = logger.bind(channel=PAYMENTS_CHANNEL)


@dataclass(frozen=True)
class CheckoutSessionData:
    session: Session
    provider_data: dict


async def create_checkout_session(
    line_items: list[dict],
    metadata: dict = None,
    *,
    success_url: str,
    customer_email: str | None = None,
    mode: str = "payment",
) -> Session:
    metadata = metadata or {}
    session_data = {
        "mode": mode,
        "success_url": success_url,
        "line_items": line_items,
        "metadata": metadata,
        "payment_intent_data": {"metadata": metadata},
    }
    if customer_email is not None:
        session_data["customer_email"] = customer_email

    session = stripe.checkout.Session.create(**session_data)
    return session


def build_membership_application_line_items(
    membership_type: "MembershipType",
    amount_cents: int,
) -> list[dict]:
    return [
        {
            "price_data": {
                "currency": "usd",
                "unit_amount": amount_cents,
                "product_data": {
                    "name": membership_type.name,
                    "description": membership_type.description,
                },
            },
            "quantity": 1,
        }
    ]


async def create_membership_application_checkout_session(
    *,
    membership_request: "MembershipRequest",
    membership_type: "MembershipType",
    payment: Payment,
    success_url: str | None = None,
) -> CheckoutSessionData:
    amount_cents = to_stripe_amount(membership_type.price_usd)
    metadata = {
        "membership_request_id": str(membership_request.id),
        "payment_id": str(payment.id),
        "payment_purpose": PaymentPurposeEnum.MEMBERSHIP_APPLICATION.value,
    }

    checkout_session = await create_checkout_session(
        build_membership_application_line_items(membership_type, amount_cents),
        metadata=metadata,
        success_url=success_url or f"{settings.FRONTEND_DOMAIN}/membership/payment-success",
    )
    return CheckoutSessionData(
        session=checkout_session,
        provider_data={
            "membership_request_id": membership_request.id,
            "payment_id": str(payment.id),
            "checkout_session_id": checkout_session.id,
            "checkout_session_status": checkout_session.status,
            "payment_intent_status": checkout_session.payment_status,
            "url": checkout_session.url,
        },
    )


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


async def create_membership_renewal_checkout_session(
    *,
    payment: Payment,
    membership_type: "MembershipType",
    user_membership: "UserMembership",
    user_email: str,
) -> CheckoutSessionData:
    amount_cents = to_stripe_amount(membership_type.price_usd)
    metadata = {
        "user_membership_id": str(user_membership.id),
        "payment_id": str(payment.id),
        "payment_purpose": PaymentPurposeEnum.MEMBERSHIP_RENEWAL.value,
    }

    checkout_session = await create_checkout_session(
        build_membership_application_line_items(membership_type, amount_cents),
        metadata=metadata,
        success_url=f"{settings.FRONTEND_DOMAIN}/membership/renewal-success",
        customer_email=user_email,
    )

    return CheckoutSessionData(
        session=checkout_session,
        provider_data={
            "user_membership_id": user_membership.id,
            "payment_id": str(payment.id),
            "checkout_session_id": checkout_session.id,
            "checkout_session_status": checkout_session.status,
            "payment_intent_status": checkout_session.payment_status,
            "url": checkout_session.url,
        },
    )


def to_stripe_amount(amount: Decimal, currency: str = "usd") -> int:
    currency = currency.lower()
    if currency == "usd":
        return int((amount * Decimal("100")).quantize(Decimal("1"), rounding=ROUND_HALF_UP))

    raise ValueError(f"Unsupported currency: {currency}")
