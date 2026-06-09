from datetime import datetime, timedelta, timezone
from typing import Annotated

from fastapi import Depends
from loguru import logger
from stripe import Event

from app.core.logging import PAYMENTS_CHANNEL
from app.domains.memberships.models import UserMembership
from app.domains.memberships.services import UserMembershipServiceDep
from app.domains.payments.models import Payment
from app.domains.payments.services import PaymentServiceDep

payments_logger = logger.bind(channel=PAYMENTS_CHANNEL)


class MembershipRenewalHandler:
    def __init__(
        self,
        user_membership_service: UserMembershipServiceDep,
        payment_service: PaymentServiceDep,
    ):
        self.__user_membership_service = user_membership_service
        self.__payment_service = payment_service

    async def on_succeeded(self, payment: Payment, event: Event) -> None:
        pass

    async def on_failed(self, payment: Payment, event: Event) -> None:
        payments_logger.info(
            "Membership request updated after failed payment: event_id={} user_membership_id={}",
            event.id,
            payment.membership_request_id,
        )

    async def on_expired(self, payment: Payment, event: Event) -> None:
        pass

    async def on_checkout_session_completed(self, payment, event: Event) -> None:
        session = event.data.object

        if session.payment_status != "paid":
            return

        user_membership_id = payment.provider_data.get("user_membership_id", None)
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

        new_expires_at = (
            user_membership.expires_at + timedelta(days=365)
            if user_membership.is_active
            else datetime.now(timezone.utc()) + timedelta(days=365)
        )

        await self.__user_membership_service.update_user_membership(
            user_membership_id,
            expires_at=new_expires_at,
        )


MembershipRenewalHandlerDep = Annotated[MembershipRenewalHandler, Depends(MembershipRenewalHandler)]
