from typing import Annotated

from fastapi import Depends
from loguru import logger
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.core.common.exceptions import NotFoundError
from app.core.logging import PAYMENTS_CHANNEL
from app.domains.memberships.exceptions import (
    CantBuyHonoraryMembership,
    MembershipAlreadyPaidError,
    MembershipApplicationCheckoutError,
    MembershipRequestCannotBeReappliedError,
)
from app.domains.memberships.models import (
    MembershipRequest,
    MembershipRequestStatusEnum,
    MembershipType,
    MembershipTypeEnum,
)
from app.domains.memberships.services import (
    MembershipRequestServiceDep,
    MembershipTypeServiceDep,
)
from app.domains.payments.models import PaymentProvider, PaymentPurposeEnum, PaymentStatusEnum
from app.domains.payments.services import PaymentServiceDep
from app.domains.payments.stripe.utils import create_membership_application_checkout_session, to_stripe_amount
from app.domains.shared.transaction_managers import TransactionManagerDep
from app.domains.users.models import User

payments_logger = logger.bind(channel=PAYMENTS_CHANNEL)


class ReapplyMembershipApplicationUseCase:
    def __init__(
        self,
        transaction_manager: TransactionManagerDep,
        membership_service: MembershipRequestServiceDep,
        membership_type_service: MembershipTypeServiceDep,
        payment_service: PaymentServiceDep,
    ):
        self.__transaction_manager = transaction_manager
        self.__membership_service = membership_service
        self.__membership_type_service = membership_type_service
        self.__payment_service = payment_service

    @staticmethod
    def __check_membership_request_rejected(membership_request: MembershipRequest):
        if membership_request.status != MembershipRequestStatusEnum.REJECTED:
            raise MembershipRequestCannotBeReappliedError("Cannot reapply not rejected membership request")

    async def __get_user_membership_request_for_update(self, user_id: int) -> MembershipRequest:
        stmt = (
            select(MembershipRequest)
            .options(selectinload(MembershipRequest.membership_type))
            .where(MembershipRequest.user_id == user_id)
            .with_for_update()
        )
        membership_request = await self.__transaction_manager.membership_requests_repository.get_first_by_kwargs(
            stmt=stmt,
        )
        if membership_request is None:
            raise NotFoundError("Membership request for the current user not found")
        return membership_request

    async def __ensure_no_succeeded_membership_application_payment(
        self,
        membership_request: MembershipRequest,
    ) -> None:
        payment = await self.__payment_service.get_succeeded_application_payment_for_request(membership_request.id)
        if payment is not None:
            raise MembershipAlreadyPaidError("Membership application payment already succeeded")

    async def __validate_membership_type_id(self, **kwargs) -> MembershipType:
        membership_type_id = kwargs.get("membership_type_id")
        if membership_type_id is None:
            raise MembershipRequestCannotBeReappliedError("No membership type id provided")

        membership_type = await self.__membership_type_service.get_membership_type_by_id(membership_type_id)
        if membership_type.type == MembershipTypeEnum.HONORARY:
            raise CantBuyHonoraryMembership("Can't purchase HONORARY membership")
        return membership_type

    async def execute(self, current_user: User, **kwargs) -> str:
        async with self.__transaction_manager:
            payments_logger.info("Membership request reapply started: user_id={}", current_user.id)
            membership_request = await self.__get_user_membership_request_for_update(current_user.id)

            self.__check_membership_request_rejected(membership_request)
            await self.__ensure_no_succeeded_membership_application_payment(membership_request)
            membership_type = await self.__validate_membership_type_id(**kwargs)

            await self.__membership_service.update_membership_request(
                membership_request.id,
                status=MembershipRequestStatusEnum.PAYMENT_PENDING,
                reviewer_id=None,
                reviewed_at=None,
                admin_comment=None,
                **kwargs,
            )

            payment = await self.__payment_service.create_payment(
                provider=PaymentProvider.STRIPE,
                amount=to_stripe_amount(membership_type.price_usd),
                status=PaymentStatusEnum.PENDING,
                purpose=PaymentPurposeEnum.MEMBERSHIP_APPLICATION,
                user_id=current_user.id,
                provider_data=None,
                membership_request_id=membership_request.id,
            )

            await self.__transaction_manager.commit()
            payments_logger.info(
                "Created membership reapply payment intent: membership_request_id={} payment_id={}",
                membership_request.id,
                payment.id,
            )

            try:
                checkout = await create_membership_application_checkout_session(
                    membership_request=membership_request,
                    membership_type=membership_type,
                    payment=payment,
                )
            except Exception as exc:
                payments_logger.exception(
                    "Failed to create reapply checkout session: membership_request_id={} payment_id={}",
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
                "Created membership request reapply: membership_request_id={} payment_id={} checkout_session_id={}",
                membership_request.id,
                payment.id,
                checkout.session.id,
            )

        return checkout.session.url


ReapplyMembershipApplicationUseCaseDep = Annotated[
    ReapplyMembershipApplicationUseCase,
    Depends(ReapplyMembershipApplicationUseCase),
]
