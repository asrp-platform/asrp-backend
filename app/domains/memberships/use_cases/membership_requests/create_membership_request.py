from typing import Annotated

from fastapi import Depends
from loguru import logger

from app.core.logging import PAYMENTS_CHANNEL
from app.domains.feedback.services import FeedbackAdditionalInfoServiceDep
from app.domains.memberships.exceptions import CantBuyHonoraryMembership, MembershipApplicationCheckoutError
from app.domains.memberships.models import MembershipRequestStatusEnum, MembershipTypeEnum
from app.domains.memberships.services import MembershipServiceDep, MembershipTypeServiceDep
from app.domains.payments.models import PaymentProvider, PaymentPurposeEnum, PaymentStatusEnum
from app.domains.payments.services import PaymentServiceDep
from app.domains.payments.stripe.utils import create_membership_application_checkout_session, to_stripe_amount
from app.domains.shared.transaction_managers import TransactionManagerDep
from app.domains.users.services import CommunicationPreferencesServiceDep

payments_logger = logger.bind(channel=PAYMENTS_CHANNEL)


class CreateUserMembershipRequestUseCase:
    def __init__(
        self,
        transaction_manager: TransactionManagerDep,
        membership_service: MembershipServiceDep,
        membership_type_service: MembershipTypeServiceDep,
        feedback_additional_info_service: FeedbackAdditionalInfoServiceDep,
        communication_preference_service: CommunicationPreferencesServiceDep,
        payment_service: PaymentServiceDep,
    ) -> None:
        self.__transaction_manager = transaction_manager
        self.__membership_service = membership_service
        self.__membership_type_service = membership_type_service
        self.__feedback_additional_info_service = feedback_additional_info_service
        self.__communication_preference_service = communication_preference_service
        self.__payment_service = payment_service

    async def execute(
        self,
        user_id: int,
        is_agrees_communications: bool,
        membership_type: MembershipTypeEnum,
        membership_request_data: dict,
        feedback_additional_info_data: dict,
    ) -> str:
        self.__check_membership_type_purchasable(membership_type)

        async with self.__transaction_manager:
            membership_request = await self.__membership_service.create_membership_request(
                user_id,
                membership_type,
                status=MembershipRequestStatusEnum.PAYMENT_PENDING,
                **membership_request_data,
            )
            # Need to get membership_request id
            await self.__transaction_manager.flush()

            await self.__feedback_additional_info_service.create_feedback_additional_info(
                user_id,
                **feedback_additional_info_data,
            )

            await self.__communication_preference_service.update_or_create_preferences(
                user_id,
                is_agrees_communications=is_agrees_communications,
            )

            membership_type = await self.__membership_type_service.get_membership_type_by_value(membership_type)
            membership_type_price_cents = to_stripe_amount(membership_type.price_usd)

            payment = await self.__payment_service.create_payment(
                provider=PaymentProvider.STRIPE,
                amount=membership_type_price_cents,
                status=PaymentStatusEnum.PENDING,
                purpose=PaymentPurposeEnum.MEMBERSHIP_APPLICATION,
                user_id=user_id,
                provider_data=None,
                membership_request_id=membership_request.id,
            )
            await self.__transaction_manager.commit()

            try:
                checkout = await create_membership_application_checkout_session(
                    membership_request=membership_request,
                    membership_type=membership_type,
                    payment=payment,
                )
            except Exception as exc:
                payments_logger.exception(
                    "Failed to create membership application checkout session: membership_request_id={} payment_id={}",
                    membership_request.id,
                    payment.id,
                )
                await self.__payment_service.update_payment(
                    payment.id,
                    status=PaymentStatusEnum.FAILED,
                    provider_data={
                        "membership_request_id": membership_request.id,
                        "payment_id": str(payment.id),
                        "error_type": "checkout_session_error",
                    },
                )
                await self.__transaction_manager.commit()
                raise MembershipApplicationCheckoutError("Failed to create checkout session") from exc

            await self.__payment_service.update_payment(payment.id, provider_data=checkout.provider_data)

            payments_logger.info(
                "Created membership request: membership_request_id={} payment_id={} checkout_session_id={}",
                membership_request.id,
                payment.id,
                checkout.session.id,
            )

        return checkout.session.url

    @staticmethod
    def __check_membership_type_purchasable(membership_type: MembershipTypeEnum):
        if membership_type == MembershipTypeEnum.HONORARY:
            raise CantBuyHonoraryMembership("Can't buy honorary membership")


CreateMembershipRequestUseCaseDep = Annotated[
    CreateUserMembershipRequestUseCase, Depends(CreateUserMembershipRequestUseCase)
]
