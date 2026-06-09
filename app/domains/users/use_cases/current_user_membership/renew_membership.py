from typing import Annotated

from fastapi import Depends
from loguru import logger

from app.core.logging import PAYMENTS_CHANNEL
from app.domains.memberships.exceptions import MembershipRenewalCheckoutError
from app.domains.memberships.models import MembershipType, UserMembership
from app.domains.memberships.services import UserMembershipServiceDep
from app.domains.payments.models import PaymentProvider, PaymentPurposeEnum, PaymentStatusEnum
from app.domains.payments.services import PaymentServiceDep
from app.domains.payments.stripe.utils import create_membership_renewal_checkout_session, to_stripe_amount
from app.domains.shared.transaction_managers import TransactionManagerDep

payments_logger = logger.bind(channel=PAYMENTS_CHANNEL)


class RenewMembershipUseCase:
    def __init__(
        self,
        transaction_manager: TransactionManagerDep,
        user_membership_service: UserMembershipServiceDep,
        payment_service: PaymentServiceDep,
    ):
        self.__tm = transaction_manager
        self.__user_membership_service = user_membership_service
        self.__payment_service = payment_service

    async def execute(self, current_user: UserMembership):
        async with self.__tm:
            current_user_membership = await self.__user_membership_service.get_user_membership_by_user_id(
                current_user.id
            )
            membership_type: MembershipType = current_user_membership.membership_type
            membership_type_price_cents = to_stripe_amount(membership_type.price_usd)

            payment = await self.__payment_service.create_payment(
                provider=PaymentProvider.STRIPE,
                amount=membership_type_price_cents,
                status=PaymentStatusEnum.PENDING,
                purpose=PaymentPurposeEnum.MEMBERSHIP_RENEWAL,
                user_id=current_user_membership.user_id,
                provider_data=None,
                membership_request_id=None,
            )
            await self.__tm.commit()

            try:
                checkout = await create_membership_renewal_checkout_session(
                    payment=payment,
                    membership_type=membership_type,
                    user_membership=current_user_membership,
                )
            except Exception as exc:
                payments_logger.exception(
                    "Failed to create membership renewal checkout session: user_membership_id={} payment_id={}",
                    current_user_membership.id,
                    payment.id,
                )
                await self.__payment_service.update_payment(
                    payment.id,
                    status=PaymentStatusEnum.FAILED,
                    provider_data={
                        "user_membership_id": current_user_membership.id,
                        "payment_id": str(payment.id),
                        "error_type": "checkout_session_error",
                    },
                )
                await self.__tm.commit()
                raise MembershipRenewalCheckoutError("Failed to create checkout session") from exc

            await self.__payment_service.update_payment(payment.id, provider_data=checkout.provider_data)

            payments_logger.info(
                "Created membership request: user_membership_id={} payment_id={} checkout_session_id={}",
                current_user_membership.id,
                payment.id,
                checkout.session.id,
            )

        return checkout.session.url


RenewMembershipUseCaseDep = Annotated[RenewMembershipUseCase, Depends(RenewMembershipUseCase)]
