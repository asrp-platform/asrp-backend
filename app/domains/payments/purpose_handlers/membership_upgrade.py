from typing import Annotated

from fastapi import Depends
from loguru import logger
from stripe import Event

from app.core.logging import PAYMENTS_CHANNEL
from app.domains.memberships.models import MembershipType, UserMembership
from app.domains.memberships.services import MembershipTypeServiceDep, UserMembershipServiceDep
from app.domains.payments.models import Payment, PaymentPurposeEnum, PaymentStatusEnum
from app.domains.payments.services import PaymentServiceDep


payments_logger = logger.bind(channel=PAYMENTS_CHANNEL)


def _get_metadata_value(metadata, key: str):
    if isinstance(metadata, dict):
        return metadata.get(key)
    return getattr(metadata, key, None)


class MembershipUpgradeHandler:
    def __init__(
        self,
        user_membership_service: UserMembershipServiceDep,
        membership_type_service: MembershipTypeServiceDep,
        payment_service: PaymentServiceDep,
    ):
        self._user_membership_service = user_membership_service
        self._membership_type_service = membership_type_service
        self._payment_service = payment_service

    async def on_succeeded(self, payment: Payment, event: Event) -> None:
        """Updates PENDING payments to EXPIRED when membership upgraded"""
        pending_renewal_payments = await self._payment_service.get_all_user_pending_payments_by_kwargs(
            user_id=payment.user_id,
            purpose=PaymentPurposeEnum.MEMBERSHIP_TYPE_UPGRADE,
        )
        expired_payment_ids = [pending_payment.id for pending_payment in pending_renewal_payments]
        await self._payment_service.update_payments_by_ids(
            expired_payment_ids,
            status=PaymentStatusEnum.EXPIRED,
        )

    async def on_failed(self, payment: Payment, event: Event) -> None:
        payments_logger.info(
            "Membership upgrade payment failed: event_id={} payment_id={} user_id={}",
            event.id,
            payment.id,
            payment.user_id,
        )

    async def on_expired(self, payment: Payment, event: Event) -> None:
        payments_logger.info(
            "Membership upgrade payment expired: event_id={} payment_id={} user_id={}",
            event.id,
            payment.id,
            payment.user_id,
        )

    async def on_checkout_session_completed(self, payment, event: Event) -> None:
        session = event.data.object

        if session.payment_status != "paid":
            return

        metadata = session.metadata or {}
        provider_data = payment.provider_data or {}
        user_membership = await self._get_user_membership(
            provider_data=provider_data,
            metadata=metadata,
            payment=payment,
            event=event,
            session=session,
        )
        if user_membership is None:
            return

        target_membership_type = await self._get_target_membership_type(
            provider_data=provider_data,
            metadata=metadata,
            payment=payment,
            event=event,
            session=session,
        )
        if target_membership_type is None:
            return

        previous_membership_type_id = user_membership.membership_type_id
        await self._user_membership_service.update_user_membership(
            user_membership.id,
            membership_type_id=target_membership_type.id,
        )
        await self._payment_service.update_payment(
            payment.id,
            provider_data={
                **provider_data,
                "user_membership_id": user_membership.id,
                "checkout_session_id": session.id,
                "checkout_session_status": getattr(session, "status", None),
                "checkout_session_payment_status": session.payment_status,
                "previous_membership_type_id": previous_membership_type_id,
                "target_membership_type_id": target_membership_type.id,
                "target_membership_type": target_membership_type.type.value,
            },
        )

        payments_logger.info(
            "Membership upgraded: event_id={} payment_id={} user_membership_id={} "
            "previous_membership_type_id={} target_membership_type_id={}",
            event.id,
            payment.id,
            user_membership.id,
            previous_membership_type_id,
            target_membership_type.id,
        )

    async def _get_user_membership(
        self,
        provider_data: dict,
        metadata: dict,
        payment: Payment,
        event: Event,
        session,
    ) -> UserMembership | None:
        user_membership_id = provider_data.get("user_membership_id") or _get_metadata_value(
            metadata, "user_membership_id"
        )
        if user_membership_id is None:
            payments_logger.warning(
                "Membership upgrade - No membership provided: payment_id={} event_id={} checkout_session_id={}",
                payment.id,
                event.id,
                session.id,
            )
            return None

        user_membership = await self._user_membership_service.get_user_membership_by_id(int(user_membership_id))
        if user_membership is None:
            payments_logger.warning(
                "Membership upgrade - Membership not found: payment_id={} event_id={} user_membership_id={}",
                payment.id,
                event.id,
                user_membership_id,
            )
            return None

        return user_membership

    async def _get_target_membership_type(
        self,
        provider_data: dict,
        metadata: dict,
        payment: Payment,
        event: Event,
        session,
    ) -> MembershipType | None:
        target_membership_type_id = provider_data.get("target_membership_type_id") or _get_metadata_value(
            metadata, "target_membership_type_id"
        )
        if target_membership_type_id is None:
            payments_logger.warning(
                "Membership upgrade - No target membership type provided: payment_id={} event_id={} "
                "checkout_session_id={}",
                payment.id,
                event.id,
                session.id,
            )
            return None

        target_membership_type = await self._membership_type_service.get_membership_type_by_id(
            membership_type_id=int(target_membership_type_id)
        )

        if target_membership_type is None:
            payments_logger.warning(
                "Membership upgrade - Target membership type not found: payment_id={} event_id={} "
                "target_membership_type_id={}",
                payment.id,
                event.id,
                target_membership_type_id,
            )
            return None

        return target_membership_type


MembershipUpgradeHandlerDep = Annotated[MembershipUpgradeHandler, Depends(MembershipUpgradeHandler)]
