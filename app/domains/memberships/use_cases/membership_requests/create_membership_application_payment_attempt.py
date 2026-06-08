from typing import Annotated

from fastapi import Depends
from loguru import logger

from app.core.common.exceptions import NotFoundError
from app.core.database.base_transaction_manager import BaseTransactionManager
from app.core.logging import PAYMENTS_CHANNEL
from app.domains.memberships.exceptions import MembershipAlreadyPaidError, MembershipApplicationCheckoutError
from app.domains.memberships.models import MembershipRequest, MembershipRequestStatusEnum
from app.domains.memberships.services import (
    MembershipRequestService,
    MembershipRequestServiceDep,
    MembershipTypeService,
    MembershipTypeServiceDep,
)
from app.domains.payments.models import PaymentProvider, PaymentPurposeEnum, PaymentStatusEnum
from app.domains.payments.services import PaymentService, PaymentServiceDep
from app.domains.payments.stripe.utils import create_membership_application_checkout_session, to_stripe_amount
from app.domains.shared.transaction_managers import TransactionManagerDep
from app.domains.users.models import User

payments_logger = logger.bind(channel=PAYMENTS_CHANNEL)


class CreateMembershipApplicationPaymentAttemptUseCase:
    def __init__(
        self,
        transaction_manager: BaseTransactionManager,
        membership_service: MembershipRequestService,
        membership_type_service: MembershipTypeService,
        payment_service: PaymentService,
    ):
        self.__transaction_manager = transaction_manager
        self.__membership_service = membership_service
        self.__membership_type_service = membership_type_service
        self.__payment_service = payment_service

    @staticmethod
    def __check_membership_already_paid(membership_request_status: MembershipRequestStatusEnum):
        if membership_request_status in (
            MembershipRequestStatusEnum.PAID,
            MembershipRequestStatusEnum.REJECTED,
            MembershipRequestStatusEnum.APPROVED,
        ):
            raise MembershipAlreadyPaidError("Membership request already paid")

    async def __ensure_no_succeeded_membership_application_payment(
        self,
        membership_request: MembershipRequest,
    ) -> None:
        payment = await self.__payment_service.get_succeeded_application_payment_for_request(membership_request.id)
        if payment is not None:
            raise MembershipAlreadyPaidError("Membership application payment already succeeded")

    async def execute(self, current_user: User):
        async with self.__transaction_manager:
            current_user_membership_request = await self.__membership_service.get_user_membership_request(
                user_id=current_user.id
            )
            if current_user_membership_request is None:
                raise NotFoundError("Membership request for the current user not found")

            self.__check_membership_already_paid(current_user_membership_request.status)
            await self.__ensure_no_succeeded_membership_application_payment(current_user_membership_request)

            membership_type = await self.__membership_type_service.get_membership_type_by_value(
                current_user_membership_request.membership_type.type
            )

            membership_type_price_cents = to_stripe_amount(membership_type.price_usd)
            payment = await self.__payment_service.create_payment(
                provider=PaymentProvider.STRIPE,
                amount=membership_type_price_cents,
                status=PaymentStatusEnum.PENDING,
                purpose=PaymentPurposeEnum.MEMBERSHIP_APPLICATION,
                user_id=current_user.id,
                provider_data=None,
                membership_request_id=current_user_membership_request.id,
            )
            # Need to get payment id
            await self.__transaction_manager.commit()

            try:
                checkout = await create_membership_application_checkout_session(
                    membership_request=current_user_membership_request,
                    membership_type=membership_type,
                    payment=payment,
                )
            except Exception as exc:
                payments_logger.exception(
                    "Failed to create membership payment attempt checkout session: membership_request_id={} payment_id={}",
                    current_user_membership_request.id,
                    payment.id,
                )
                await self.__payment_service.update_payment(
                    payment.id,
                    status=PaymentStatusEnum.FAILED,
                    provider_data={
                        "membership_request_id": current_user_membership_request.id,
                        "payment_id": str(payment.id),
                        "error_type": "checkout_session_error",
                    },
                )
                await self.__transaction_manager.commit()
                raise MembershipApplicationCheckoutError("Failed to create checkout session") from exc

            await self.__payment_service.update_payment(payment.id, provider_data=checkout.provider_data)

            payments_logger.info(
                "Retry membership request payment: membership_request_id={} payment_id={} checkout_session_id={}",
                current_user_membership_request.id,
                payment.id,
                checkout.session.id,
            )

        return checkout.session.url


def get_use_case(
    transaction_manager: TransactionManagerDep,
    membership_service: MembershipRequestServiceDep,
    membership_type_service: MembershipTypeServiceDep,
    payment_service: PaymentServiceDep,
) -> CreateMembershipApplicationPaymentAttemptUseCase:
    return CreateMembershipApplicationPaymentAttemptUseCase(
        transaction_manager,
        membership_service,
        membership_type_service,
        payment_service,
    )


CreateMembershipApplicationPaymentAttemptUseCaseDep = Annotated[
    CreateMembershipApplicationPaymentAttemptUseCase, Depends(get_use_case)
]
