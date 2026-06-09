from datetime import datetime, timedelta, timezone
from typing import Annotated

from fastapi import Depends
from loguru import logger
from stripe import Event

from app.core.logging import PAYMENTS_CHANNEL
from app.domains.memberships.models import UserMembership
from app.domains.memberships.services import UserMembershipServiceDep
from app.domains.payments.models import Payment, PaymentStatusEnum
from app.domains.payments.services import PaymentServiceDep

payments_logger = logger.bind(channel=PAYMENTS_CHANNEL)


def _get_metadata_value(metadata, key: str):
    if isinstance(metadata, dict):
        return metadata.get(key)
    return getattr(metadata, key, None)


class MembershipRenewalHandler:
    def __init__(
        self,
        user_membership_service: UserMembershipServiceDep,
        payment_service: PaymentServiceDep,
    ):
        self.__user_membership_service = user_membership_service
        self.__payment_service = payment_service

    async def on_succeeded(self, payment: Payment, event: Event) -> None:
        pending_renewal_payments = await self.__payment_service.get_pending_membership_renewal_user_payment(
            user_id=payment.user_id
        )
        expired_payment_ids = [payment.id for payment in pending_renewal_payments]
        await self.__payment_service.update_payments_by_ids(
            expired_payment_ids,
            status=PaymentStatusEnum.EXPIRED,
        )

    async def on_failed(self, payment: Payment, event: Event) -> None:
        payments_logger.info(
            "Membership renewal payment failed: event_id={} payment_id={} user_id={}",
            event.id,
            payment.id,
            payment.user_id,
        )

    async def on_expired(self, payment: Payment, event: Event) -> None:
        payments_logger.info(
            "Membership renewal payment expired: event_id={} payment_id={} user_id={}",
            event.id,
            payment.id,
            payment.user_id,
        )

    async def on_checkout_session_completed(self, payment, event: Event) -> None:
        session = event.data.object

        if session.payment_status != "paid":
            return

        provider_data = payment.provider_data or {}

        metadata = session.metadata or {}
        user_membership_id = provider_data.get("user_membership_id") or _get_metadata_value(
            metadata, "user_membership_id"
        )
        if user_membership_id is None:
            payments_logger.warning(
                "User membership renewal - No membership provided: payment_id={} event_id={} checkout_session_id={}",
                payment.id,
                event.id,
                session.id,
            )
            return
        user_membership: UserMembership = await self.__user_membership_service.get_user_membership_by_id(
            user_membership_id
        )
        if user_membership is None:
            payments_logger.warning(
                "User membership renewal - Membership not found: payment_id={} event_id={} user_membership_id={}",
                payment.id,
                event.id,
                user_membership_id,
            )
            return

        now = datetime.now(timezone.utc)
        renewal_starts_at = max(user_membership.expires_at, now)
        new_expires_at = renewal_starts_at + timedelta(days=user_membership.membership_type.duration)

        await self.__user_membership_service.update_user_membership(
            user_membership_id,
            expires_at=new_expires_at,
        )
        await self.__payment_service.update_payment(
            payment.id,
            provider_data={
                **provider_data,
                "user_membership_id": user_membership.id,
                "checkout_session_id": session.id,
                "checkout_session_status": getattr(session, "status", None),
                "checkout_session_payment_status": session.payment_status,
                "previous_expires_at": user_membership.expires_at.isoformat(),
                "new_expires_at": new_expires_at.isoformat(),
            },
        )

        payments_logger.info(
            "Membership renewed: event_id={} payment_id={} user_membership_id={} previous_expires_at={} "
            "new_expires_at={}",
            event.id,
            payment.id,
            user_membership.id,
            user_membership.expires_at,
            new_expires_at,
        )


MembershipRenewalHandlerDep = Annotated[MembershipRenewalHandler, Depends(MembershipRenewalHandler)]
