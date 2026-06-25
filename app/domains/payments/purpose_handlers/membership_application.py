from typing import Annotated

from fastapi import Depends
from loguru import logger
from stripe import Event

from app.core.logging import PAYMENTS_CHANNEL
from app.domains.emails.common.messages import build_membership_application_html
from app.domains.emails.email_queue import EmailQueueDep
from app.domains.memberships.models import MembershipRequestStatusEnum
from app.domains.memberships.services import MembershipRequestServiceDep
from app.domains.payments.models import Payment, PaymentStatusEnum
from app.domains.payments.services import PaymentServiceDep
from app.domains.users.models import User
from app.domains.users.services import UserServiceDep


payments_logger = logger.bind(channel=PAYMENTS_CHANNEL)


class MembershipApplicationHandler:
    def __init__(
        self,
        membership_service: MembershipRequestServiceDep,
        payment_service: PaymentServiceDep,
        email_queue: EmailQueueDep,
        user_service: UserServiceDep,
    ):
        self.__membership_service = membership_service
        self.__payment_service = payment_service
        self.__email_queue = email_queue
        self.__user_service = user_service

    async def on_succeeded(self, payment: Payment, event: Event) -> None:
        pending_application_payments = await self.__payment_service.get_pending_membership_application_user_payment(
            user_id=payment.user_id
        )
        expired_payment_ids = [payment.id for payment in pending_application_payments]
        await self.__payment_service.update_payments_by_ids(
            expired_payment_ids,
            status=PaymentStatusEnum.EXPIRED,
        )

    async def on_failed(self, payment: Payment, event: Event) -> None:
        await self.__membership_service.update_membership_request(
            payment.membership_request_id, status=MembershipRequestStatusEnum.PAYMENT_FAILED
        )
        payments_logger.info(
            "Membership request updated after failed payment: event_id={} membership_request_id={}",
            event.id,
            payment.membership_request_id,
        )

    async def on_expired(self, payment: Payment, event: Event) -> None:
        payments_logger.info(
            "Membership application payment expired: event_id={} payment_id={}",
            event.id,
            payment.id,
        )

    async def on_checkout_session_completed(self, payment, event: Event) -> None:
        session = event.data.object

        if session.payment_status != "paid":
            return

        await self.__membership_service.update_membership_request(
            payment.membership_request_id, status=MembershipRequestStatusEnum.PAID
        )
        user: User = await self.__user_service._get_user_by_kwargs(id=payment.user_id)
        subject, body = build_membership_application_html(user.full_name)
        await self.__email_queue.send_email(to=user.email, subject=subject, body=body)


MembershipApplicationHandlerDep = Annotated[MembershipApplicationHandler, Depends(MembershipApplicationHandler)]
