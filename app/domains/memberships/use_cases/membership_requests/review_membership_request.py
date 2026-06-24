import asyncio
from datetime import datetime, timedelta, timezone
from typing import Annotated

import stripe
from fastapi import Depends
from loguru import logger

from app.core.config import settings
from app.core.logging import PAYMENTS_CHANNEL
from app.core.utils.permissions import check_permissions
from app.domains.emails.common.messages import (
    build_membership_application_approved_html,
    build_membership_application_rejected_html,
)
from app.domains.emails.email_queue import EmailQueueDep
from app.domains.memberships.exceptions import MissingMembershipRequestPayment, MissingRejectingCommentError
from app.domains.memberships.models import MembershipRequestStatusEnum
from app.domains.memberships.services import (
    MembershipRequestServiceDep,
    UserMembershipServiceDep,
)
from app.domains.payments.models import Payment, PaymentStatusEnum
from app.domains.payments.services import PaymentServiceDep
from app.domains.payments.stripe.utils import create_stripe_refund
from app.domains.shared.transaction_managers import TransactionManagerDep
from app.domains.users.models import User
from app.domains.users.services import UserServiceDep


payments_logger = logger.bind(channel=PAYMENTS_CHANNEL)


class ReviewMembershipRequestUseCase:
    def __init__(
        self,
        transaction_manager: TransactionManagerDep,
        membership_request_service: MembershipRequestServiceDep,
        user_membership_service: UserMembershipServiceDep,
        payment_service: PaymentServiceDep,
        user_service: UserServiceDep,
        email_queue: EmailQueueDep,
    ):
        self.__transaction_manager = transaction_manager
        self.__membership_request_service = membership_request_service
        self.__user_membership_service = user_membership_service
        self.__payment_service = payment_service
        self.__user_service = user_service
        self.__email_queue = email_queue

    async def __approve_membership_request(
        self,
        membership_request_id: int,
        reviewer: User,
        **kwargs,
    ) -> None:
        """
        Updates MembershipRequest: status, reviewer_id, reviewed_at
        Creates user membership
        """
        membership_request = await self.__membership_request_service.update_membership_request(
            membership_request_id, reviewer_id=reviewer.id, reviewed_at=datetime.now(timezone.utc), **kwargs
        )
        await self.__user_membership_service.create_user_membership(
            user_id=membership_request.user_id,
            expires_at=datetime.now(timezone.utc) + timedelta(days=365),
            membership_request_id=membership_request.id,
            membership_type_id=membership_request.membership_type_id,
        )

    async def __reject_membership_request(
        self,
        membership_request_id: int,
        reviewer: User,
        **kwargs,
    ) -> None:
        """
        Rejects a membership request and starts a Stripe refund if money was already captured.

        The refund is split into durable steps:
        1. Persist the rejected MembershipRequest and REFUND_REQUESTED intent, then commit.
        2. Call Stripe with a stable idempotency key and persist Stripe's refund result.

        Stripe and our database cannot share one transaction. If Stripe succeeds but our final
        update fails, the committed refund intent plus idempotency key let us retry/reconcile
        safely without creating a duplicate refund.
        """
        admin_comment = kwargs.get("admin_comment")

        if admin_comment is None:
            raise MissingRejectingCommentError("When status is REJECTED admin_comment must be provided")

        membership_request = await self.__membership_request_service.get_membership_request_by_id(membership_request_id)
        succeeded_payment = await self.__payment_service.get_succeeded_application_payment_for_request(
            membership_request.id,
        )

        await self.__membership_request_service.update_membership_request(
            membership_request_id, reviewer_id=reviewer.id, reviewed_at=datetime.now(timezone.utc), **kwargs
        )

        if succeeded_payment is None:
            payments_logger.info(
                "Refund skipped. Succeeded payment not found: membership_request_id={} reviewer_id={}",
                membership_request_id,
                reviewer.id,
            )
            return

        idempotency_key = await self.__save_refund_request(succeeded_payment, reviewer)
        await self.__transaction_manager.commit()

        try:
            refund = await asyncio.to_thread(create_stripe_refund, succeeded_payment, idempotency_key)
        except stripe.error.APIConnectionError:
            await self.__save_refund_error(
                succeeded_payment,
                idempotency_key=idempotency_key,
                refund_status="UNKNOWN",
                error_type="stripe_api_connection_error",
            )
            await self.__transaction_manager.commit()
            raise
        except stripe.error.StripeError:
            await self.__save_refund_error(
                succeeded_payment,
                idempotency_key=idempotency_key,
                refund_status="FAILED",
                error_type="stripe_api_error",
            )
            await self.__transaction_manager.commit()
            raise
        except Exception:
            await self.__save_refund_error(
                succeeded_payment,
                idempotency_key=idempotency_key,
                refund_status="FAILED",
                error_type="refund_error",
            )
            await self.__transaction_manager.commit()
            raise

        payments_logger.info(
            "Stripe refund created: payment_id={} membership_request_id={} refund_id={} refund_status={} "
            "idempotency_key={}",
            succeeded_payment.id,
            succeeded_payment.membership_request_id,
            refund.id,
            refund.status,
            idempotency_key,
        )

        await self.__save_refund_result(succeeded_payment, refund, idempotency_key)

    async def __save_refund_request(self, payment: Payment, reviewer: User) -> str:
        """Save a durable refund intent before calling Stripe."""
        idempotency_key = f"refund-payment-{payment.id}"
        await self.__payment_service.update_payment(
            payment.id,
            provider_data={
                **(payment.provider_data or {}),
                "refund": {
                    "status": "REFUND_REQUESTED",
                    "idempotency_key": idempotency_key,
                    "requested_by_admin_id": reviewer.id,
                    "reason": "membership_request_rejected",
                },
            },
        )
        payments_logger.info(
            "Refund requested: payment_id={} membership_request_id={} reviewer_id={} idempotency_key={}",
            payment.id,
            payment.membership_request_id,
            reviewer.id,
            idempotency_key,
        )
        return idempotency_key

    async def __save_refund_result(self, payment: Payment, refund, idempotency_key: str) -> None:
        """Persist Stripe's response; mark payment REFUNDED only after Stripe says succeeded."""
        payment_status = PaymentStatusEnum.REFUNDED if refund.status == "succeeded" else payment.status
        try:
            await self.__payment_service.update_payment(
                payment.id,
                status=payment_status,
                provider_data={
                    **(payment.provider_data or {}),
                    "refund": {
                        "id": refund.id,
                        "status": refund.status,
                        "amount": refund.amount,
                        "currency": refund.currency,
                        "reason": refund.reason,
                        "failure_reason": getattr(refund, "failure_reason", None),
                        "idempotency_key": idempotency_key,
                    },
                },
            )
        except Exception:
            payments_logger.exception(
                """
                Failed to persist refund result:
                payment_id={} membership_request_id={} refund_id={} refund_status={} idempotency_key={}
                """,
                payment.id,
                payment.membership_request_id,
                refund.id,
                refund.status,
                idempotency_key,
            )
            raise

    async def __save_refund_error(
        self,
        payment: Payment,
        *,
        idempotency_key: str,
        refund_status: str,
        error_type: str,
    ) -> None:
        try:
            await self.__payment_service.update_payment(
                payment.id,
                provider_data={
                    **(payment.provider_data or {}),
                    "refund": {
                        **((payment.provider_data or {}).get("refund") or {}),
                        "status": refund_status,
                        "error_type": error_type,
                        "idempotency_key": idempotency_key,
                    },
                },
            )
        except Exception:
            payments_logger.exception(
                "Failed to persist refund error: payment_id={} membership_request_id={} refund_status={} error_type={"
                "} idempotency_key={}",
                payment.id,
                payment.membership_request_id,
                refund_status,
                error_type,
                idempotency_key,
            )

    async def __check_membership_request_paid(self, membership_request_id: int):
        membership_request = await self.__membership_request_service.get_membership_request_by_id(membership_request_id)
        if membership_request.status != MembershipRequestStatusEnum.PAID:
            raise MissingMembershipRequestPayment("Can't review approve or reject unpaid membership request")
        return membership_request

    async def execute(
        self,
        membership_request_id: int,
        reviewer: User,
        permissions: list[str],
        **kwargs,
    ):
        """kwargs may include (status) when approved or (status, admin_comment) when rejected"""
        email_payload = None

        async with self.__transaction_manager:
            check_permissions("memberships.update", permissions)
            membership_request = await self.__check_membership_request_paid(membership_request_id)
            user = await self.__user_service._get_user_by_kwargs(id=membership_request.user_id)
            approval_status = kwargs.get("status")

            if approval_status == MembershipRequestStatusEnum.APPROVED:
                await self.__approve_membership_request(membership_request_id, reviewer, **kwargs)
                subject, body = build_membership_application_approved_html(
                    full_name=user.full_name, login_link=f"{settings.FRONTEND_DOMAIN}/login"
                )
                email_payload = (user.email, subject, body)

            elif approval_status == MembershipRequestStatusEnum.REJECTED:
                await self.__reject_membership_request(membership_request_id, reviewer, **kwargs)
                subject, body = build_membership_application_rejected_html(user.full_name)
                email_payload = (user.email, subject, body)

        if email_payload is not None:
            email_to, subject, body = email_payload
            await self.__email_queue.send_email(to=email_to, subject=subject, body=body)


ReviewMembershipRequestUseCaseDep = Annotated[ReviewMembershipRequestUseCase, Depends(ReviewMembershipRequestUseCase)]
