from typing import Annotated

from fastapi import Depends
from loguru import logger
from stripe import Event

from app.core.logging import PAYMENTS_CHANNEL
from app.domains.payments.models import Payment


payments_logger = logger.bind(channel=PAYMENTS_CHANNEL)


class DonationHandler:
    async def on_succeeded(self, payment: Payment, event: Event) -> None:
        payments_logger.info(
            "Donation payment succeeded: event_id={} payment_id={} amount={} currency={}",
            event.id,
            payment.id,
            payment.amount,
            payment.currency,
        )

    async def on_failed(self, payment: Payment, event: Event) -> None:
        payments_logger.info(
            "Donation payment failed: event_id={} payment_id={}",
            event.id,
            payment.id,
        )

    async def on_expired(self, payment: Payment, event: Event) -> None:
        payments_logger.info(
            "Donation payment expired: event_id={} payment_id={}",
            event.id,
            payment.id,
        )

    async def on_checkout_session_completed(self, payment: Payment, event: Event) -> None:
        session = event.data.object
        payments_logger.info(
            "Donation checkout session completed: event_id={} payment_id={} "
            "checkout_session_id={} checkout_session_status={} payment_status={}",
            event.id,
            payment.id,
            session.id,
            getattr(session, "status", None),
            getattr(session, "payment_status", None),
        )


DonationHandlerDep = Annotated[DonationHandler, Depends()]
