from typing import Annotated

from fastapi import Depends
from loguru import logger

from app.core.logging import PAYMENTS_CHANNEL
from app.domains.memberships.exceptions import (
    CantChangeToHonoraryMembershipError,
    CheckoutSessionCreationError,
    InvalidMembershipTypeUpgradeError,
    SameMembershipTypeChangeRequestError,
)
from app.domains.memberships.models import MembershipType, MembershipTypeEnum, UserMembership
from app.domains.memberships.services import MembershipTypeServiceDep
from app.domains.payments.models import PaymentProvider, PaymentPurposeEnum, PaymentStatusEnum
from app.domains.payments.services import PaymentServiceDep
from app.domains.payments.stripe.utils import create_membership_upgrade_checkout_session, to_stripe_amount
from app.domains.shared.transaction_managers import TransactionManagerDep
from app.domains.users.models import User


payments_logger = logger.bind(channel=PAYMENTS_CHANNEL)


class UpgradeMembershipUseCase:
    def __init__(
        self,
        transaction_manager: TransactionManagerDep,
        membership_type_service: MembershipTypeServiceDep,
        payment_service: PaymentServiceDep,
    ):
        self._tm = transaction_manager
        self._membership_type_service = membership_type_service
        self._payment_service = payment_service

    async def execute(
        self,
        current_user_membership: UserMembership,
        current_user: User,
        target_membership_type_id: int,
    ) -> str:
        # membership comes from CurrentUserMembershipDep which loads membership_type
        current_membership_type = current_user_membership.membership_type

        async with self._tm:
            # Service method raises not found error membership type not found
            target_membership_type = await self._membership_type_service.get_membership_type_by_id(
                target_membership_type_id
            )

            self.check_can_upgrade(current_membership_type, target_membership_type)
            self.check_upgrade_correctness(current_membership_type, target_membership_type)

            amount_cents = to_stripe_amount(target_membership_type.price_usd - current_membership_type.price_usd)

            payment = await self._payment_service.create_payment(
                provider=PaymentProvider.STRIPE,
                amount=amount_cents,
                status=PaymentStatusEnum.PENDING,
                purpose=PaymentPurposeEnum.MEMBERSHIP_TYPE_UPGRADE,
                user_id=current_user.id,
                provider_data=None,
            )
            await self._tm.commit()

            try:
                checkout = await create_membership_upgrade_checkout_session(
                    payment=payment,
                    amount_cents=int(amount_cents),
                    current_membership_type=current_membership_type,
                    target_membership_type=target_membership_type,
                    user_membership=current_user_membership,
                    user_email=current_user.email,
                )
            except Exception as exc:
                payments_logger.exception(
                    "Failed to create membership upgrade checkout session: user_membership_id={} payment_id={}",
                    current_user_membership.id,
                    payment.id,
                )
                await self._payment_service.update_payment(
                    payment.id,
                    status=PaymentStatusEnum.FAILED,
                    provider_data={
                        "user_membership_id": current_user_membership.id,
                        "payment_id": str(payment.id),
                        "error_type": "checkout_session_error",
                    },
                )
                await self._tm.commit()
                raise CheckoutSessionCreationError("Failed to create checkout session") from exc

            provider_data = {
                **checkout.provider_data,
                "current_membership_type_id": current_membership_type.id,
                "target_membership_type_id": target_membership_type.id,
            }

            await self._payment_service.update_payment(payment.id, provider_data=provider_data)

            payments_logger.info(
                "Created membership upgrade checkout session: user_membership_id={} payment_id={} "
                "checkout_session_id={}",
                current_user_membership.id,
                payment.id,
                checkout.session.id,
            )

        return checkout.session.url

    @staticmethod
    def check_can_upgrade(current_membership_type: MembershipType, target_membership_type: MembershipType):
        if target_membership_type.id == current_membership_type.id:
            raise SameMembershipTypeChangeRequestError("Can't change membership type for the same type")
        if target_membership_type.type == MembershipTypeEnum.HONORARY:
            raise CantChangeToHonoraryMembershipError("Can't change membership type to HONORARY")
        if not target_membership_type.is_purchasable:
            raise InvalidMembershipTypeUpgradeError("Invalid upgrade type")
        if current_membership_type.type in [MembershipTypeEnum.HONORARY, MembershipTypeEnum.ACTIVE]:
            raise InvalidMembershipTypeUpgradeError("Invalid upgrade type")

    @staticmethod
    def check_upgrade_correctness(current_membership_type: MembershipType, target_membership_type: MembershipType):
        difference = target_membership_type.price_usd - current_membership_type.price_usd
        if difference <= 0:
            raise InvalidMembershipTypeUpgradeError("Invalid upgrade type")


UpgradeMembershipUseCaseDep = Annotated[UpgradeMembershipUseCase, Depends()]
