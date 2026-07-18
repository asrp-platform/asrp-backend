from decimal import ROUND_HALF_UP, Decimal
from typing import Annotated

from fastapi import Depends
from loguru import logger

from app.core.config import settings
from app.core.logging import PAYMENTS_CHANNEL
from app.domains.payments.models import Payment, PaymentProvider, PaymentPurposeEnum, PaymentStatusEnum
from app.domains.payments.services import PaymentServiceDep
from app.domains.payments.stripe.utils import create_checkout_session
from app.domains.shared.transaction_managers import TransactionManagerDep


payments_logger = logger.bind(channel=PAYMENTS_CHANNEL)


class MakeDonationUseCase:
    def __init__(
        self,
        transaction_manager: TransactionManagerDep,
        payment_service: PaymentServiceDep,
    ):
        self._tm = transaction_manager
        self._payment_service = payment_service

    async def execute(self, price_usd: Decimal, customer_email: str) -> str:
        amount_in_cents = int((price_usd * 100).quantize(Decimal("1"), rounding=ROUND_HALF_UP))

        async with self._tm:
            payment: Payment = await self._payment_service.create_payment(
                provider=PaymentProvider.STRIPE,
                amount=amount_in_cents,
                status=PaymentStatusEnum.PENDING,
                purpose=PaymentPurposeEnum.DONATION,
                user_id=None,
                provider_data=None,
            )

            await self._tm.flush()

            metadata = {"payment_id": payment.id, "payment_purpose": PaymentPurposeEnum.DONATION.value}
            try:
                checkout_session = await create_checkout_session(
                    line_items=self._build_donation_line_items(amount_in_cents),
                    metadata=metadata,
                    success_url=f"{settings.FRONTEND_DOMAIN}/donations-and-sponsorship/payment-success",
                    customer_email=customer_email,
                    mode="payment",
                    submit_type="donate",
                )

            except Exception as exc:
                payments_logger.exception(
                    "Failed to donation checkout session: payment_id={}",
                    payment.id,
                )
                await self._payment_service.update_payment(
                    payment.id,
                    status=PaymentStatusEnum.FAILED,
                    provider_data={
                        "payment_id": str(payment.id),
                        "error_type": "checkout_session_error",
                    },
                )
                await self._tm.commit()
                raise exc

            provider_data = {
                "payment_id": str(payment.id),
                "checkout_session_id": checkout_session.id,
                "checkout_session_status": checkout_session.status,
                "payment_intent_status": checkout_session.payment_status,
                "url": checkout_session.url,
            }

            await self._payment_service.update_payment(payment.id, provider_data=provider_data)

            payments_logger.info(
                "Created one-time donation: payment_id={} checkout_session_id={}",
                payment.id,
                checkout_session.id,
            )

            return checkout_session.url

    @staticmethod
    def _build_donation_line_items(amount_in_cents: int) -> list[dict]:
        return [
            {
                "price_data": {
                    "currency": "usd",
                    "unit_amount": amount_in_cents,
                    "product_data": {"name": "One-time donation to ASRP", "description": "One-time donation"},
                },
                "quantity": 1,
            },
        ]


MakeDonationUseCaseDep = Annotated[MakeDonationUseCase, Depends()]
