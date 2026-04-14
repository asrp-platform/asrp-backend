from typing import Annotated

from fastapi import Depends

from app.core.config import settings
from app.domains.feedback.services import (
    FeedbackAdditionalInfoService,
    FeedbackAdditionalInfoServiceDep,
    get_feedback_additional_info_service,
)
from app.domains.memberships.infrastructure import MembershipsTransactionManagerBase, get_memberships_unit_of_work
from app.domains.memberships.models import MembershipRequestStatusEnum, MembershipTypeEnum
from app.domains.memberships.services import MembershipService, MembershipServiceDep
from app.domains.payments.models import PaymentProvider, PaymentPurposeEnum, PaymentStatusEnum
from app.domains.payments.services import PaymentServiceDep
from app.domains.payments.stripe.utils import create_checkout_session, to_stripe_amount
from app.domains.users.services import (
    CommunicationPreferencesService,
    CommunicationPreferencesServiceDep,
    get_communication_preferences_service,
)


class CreateUserMembershipRequestUseCase:
    def __init__(
        self,
        uow: MembershipsTransactionManagerBase,
        membership_service: MembershipService,
        feedback_additional_info_service: FeedbackAdditionalInfoService,
        communication_preference_service: CommunicationPreferencesService,
        payment_service: PaymentServiceDep,
    ) -> None:
        self.uow = uow
        self.membership_service = membership_service
        self.feedback_additional_info_service = feedback_additional_info_service
        self.communication_preference_service = communication_preference_service
        self.payment_service = payment_service

    async def execute(
        self,
        user_id: int,
        is_agrees_communications: bool,
        membership_type: MembershipTypeEnum,
        membership_request_data: dict,
        feedback_additional_info_data: dict,
    ) -> str:
        async with self.uow:
            membership_request = await self.membership_service.create_membership_request(
                user_id,
                membership_type,
                status=MembershipRequestStatusEnum.PAYMENT_PENDING,
                **membership_request_data,
            )

            await self.feedback_additional_info_service.create_feedback_additional_info(
                user_id,
                **feedback_additional_info_data,
            )

            await self.communication_preference_service.update_or_create_preferences(
                user_id,
                is_agrees_communications=is_agrees_communications,
            )

            membership_type = await self.membership_service.get_membership_type(membership_type)
            membership_type_price_cents = to_stripe_amount(membership_type.price_usd)

            membership_type_line_items = [
                {
                    "price_data": {
                        "currency": "usd",
                        "unit_amount": membership_type_price_cents,
                        "product_data": {
                            "name": membership_type.name,
                            "description": membership_type.description,
                        },
                    },
                    "quantity": 1,
                }
            ]
            payment = await self.payment_service.create_payment(
                provider=PaymentProvider.STRIPE,
                amount=membership_type_price_cents,
                status=PaymentStatusEnum.PENDING,
                purpose=PaymentPurposeEnum.MEMBERSHIP_APPLICATION,
                user_id=user_id,
                provider_data=None,
            )
            # Needed to get payment id
            await self.uow._session.flush()

            payment_metadata = {
                "membership_request_id": membership_request.id,
                "payment_id": str(payment.id),
                "payment_purpose": PaymentPurposeEnum.MEMBERSHIP_APPLICATION,
            }

            checkout_session = await create_checkout_session(
                membership_type_line_items,
                metadata=payment_metadata,
                success_url=f"{settings.FRONTEND_DOMAIN}/membership/payment-success",
            )

            provider_data = {
                "payment_id": str(payment.id),
                "checkout_session_id": checkout_session.id,
                "checkout_session_status": checkout_session.status,
                "payment_intent_status": checkout_session.payment_status,
                "url": checkout_session.url,
            }

            await self.payment_service.update_payment(payment.id, provider_data=provider_data)

        return checkout_session.url


def get_create_membership_request_use_case(
    uow: Annotated[MembershipsTransactionManagerBase, Depends(get_memberships_unit_of_work)],
    membership_service: MembershipServiceDep,
    feedback_additional_info_service: Annotated[
        FeedbackAdditionalInfoServiceDep, Depends(get_feedback_additional_info_service)
    ],
    communication_preference_service: Annotated[
        CommunicationPreferencesServiceDep, Depends(get_communication_preferences_service)
    ],
    payment_service: PaymentServiceDep,
) -> CreateUserMembershipRequestUseCase:
    return CreateUserMembershipRequestUseCase(
        uow, membership_service, feedback_additional_info_service, communication_preference_service, payment_service
    )


CreateMembershipRequestUseCaseDep = Annotated[
    CreateUserMembershipRequestUseCase, Depends(get_create_membership_request_use_case)
]
