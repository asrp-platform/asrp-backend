from datetime import datetime, timezone
from typing import Annotated

from fastapi import Depends

from app.core.common.exceptions import NotFoundError
from app.domains.memberships.models import UserMembership
from app.domains.memberships.schemas.user_memberships import (
    MembershipConfirmationReportSchema,
    MembershipHistoryEventSchema,
    MembershipHistoryEventTypeEnum,
    MembershipStatusEnum,
)
from app.domains.memberships.services import (
    MembershipRequestServiceDep,
    MembershipTypeChangeServiceDep,
    MembershipTypeServiceDep,
    UserMembershipServiceDep,
)
from app.domains.payments.models import Payment, PaymentPurposeEnum
from app.domains.payments.services import PaymentServiceDep
from app.domains.shared.transaction_managers import TransactionManagerDep
from app.domains.users.models import User
from app.domains.users.use_cases.current_user_membership.get_membership_confirmation import format_membership_id


class GetMembershipConfirmationReportUseCase:
    def __init__(
        self,
        transaction_manager: TransactionManagerDep,
        user_membership_service: UserMembershipServiceDep,
        membership_request_service: MembershipRequestServiceDep,
        membership_type_service: MembershipTypeServiceDep,
        membership_type_change_service: MembershipTypeChangeServiceDep,
        payment_service: PaymentServiceDep,
    ):
        self.__tm = transaction_manager
        self.__user_membership_service = user_membership_service
        self.__membership_request_service = membership_request_service
        self.__membership_type_service = membership_type_service
        self.__membership_type_change_service = membership_type_change_service
        self.__payment_service = payment_service

    async def execute(self, current_user: User) -> MembershipConfirmationReportSchema:
        async with self.__tm:
            membership = await self.__user_membership_service.get_user_membership_by_user_id(current_user.id)
            if membership is None:
                raise NotFoundError("Membership for the current user not found")

            membership_request = await self.__membership_request_service.get_membership_request_by_id(
                membership.membership_request_id
            )
            membership_types = await self.__membership_type_service.get_membership_types()
            type_names = {
                membership_type.id: membership_type.name or membership_type.type.value
                for membership_type in membership_types
            }
            type_changes = await self.__membership_type_change_service.get_approved_membership_type_changes(
                membership.id
            )
            payments = await self.__payment_service.get_succeeded_membership_history_payments(current_user.id)

            history = [
                MembershipHistoryEventSchema(
                    event_type=MembershipHistoryEventTypeEnum.ACTIVATED,
                    occurred_at=membership.created_at,
                    membership_type=(
                        membership_request.membership_type.name or membership_request.membership_type.type.value
                    ),
                )
            ]
            history.extend(self.__build_payment_events(payments, type_names))
            history.extend(
                MembershipHistoryEventSchema(
                    event_type=MembershipHistoryEventTypeEnum.TYPE_CHANGED,
                    occurred_at=type_change.updated_at,
                    membership_type=(
                        type_change.target_membership_type.name or type_change.target_membership_type.type.value
                    ),
                )
                for type_change in type_changes
            )
            history.extend(self.__build_restriction_events(membership))
            history.sort(key=lambda event: event.occurred_at)

            return MembershipConfirmationReportSchema(
                member_name=current_user.full_name,
                membership_type=membership.membership_type.name or membership.membership_type.type.value,
                membership_id=format_membership_id(membership),
                status=self.__get_status(membership),
                member_since=membership.created_at,
                valid_through=membership.expires_at,
                issued_at=datetime.now(timezone.utc),
                history=history,
            )

    def __build_payment_events(
        self,
        payments: list[Payment],
        type_names: dict[int, str],
    ) -> list[MembershipHistoryEventSchema]:
        events = []
        for payment in payments:
            provider_data = payment.provider_data or {}
            if payment.purpose == PaymentPurposeEnum.MEMBERSHIP_RENEWAL:
                previous_valid_through = self.__parse_datetime(provider_data.get("previous_expires_at"))
                valid_through = self.__parse_datetime(provider_data.get("new_expires_at"))
                if previous_valid_through is None or valid_through is None:
                    continue
                events.append(
                    MembershipHistoryEventSchema(
                        event_type=MembershipHistoryEventTypeEnum.RENEWED,
                        occurred_at=payment.updated_at,
                        previous_valid_through=previous_valid_through,
                        valid_through=valid_through,
                    )
                )
            elif payment.purpose == PaymentPurposeEnum.MEMBERSHIP_TYPE_UPGRADE:
                membership_type = self.__get_type_name(
                    provider_data.get("target_membership_type_id"),
                    type_names,
                    provider_data.get("target_membership_type"),
                )
                if membership_type is None:
                    continue
                events.append(
                    MembershipHistoryEventSchema(
                        event_type=MembershipHistoryEventTypeEnum.TYPE_CHANGED,
                        occurred_at=payment.updated_at,
                        previous_membership_type=self.__get_type_name(
                            provider_data.get("previous_membership_type_id"),
                            type_names,
                        ),
                        membership_type=membership_type,
                    )
                )
        return events

    @staticmethod
    def __build_restriction_events(membership: UserMembership) -> list[MembershipHistoryEventSchema]:
        events = []
        if membership.suspended_at is not None:
            events.append(
                MembershipHistoryEventSchema(
                    event_type=MembershipHistoryEventTypeEnum.SUSPENDED,
                    occurred_at=membership.suspended_at,
                    suspended_until=membership.suspended_until,
                    reason=membership.suspension_reason,
                )
            )
        if membership.terminated_at is not None:
            events.append(
                MembershipHistoryEventSchema(
                    event_type=MembershipHistoryEventTypeEnum.TERMINATED,
                    occurred_at=membership.terminated_at,
                    reason=membership.termination_reason,
                )
            )
        return events

    @staticmethod
    def __get_status(membership: UserMembership) -> MembershipStatusEnum:
        if membership.terminated:
            return MembershipStatusEnum.TERMINATED
        if membership.is_suspended:
            return MembershipStatusEnum.SUSPENDED
        if not membership.is_active:
            return MembershipStatusEnum.EXPIRED
        return MembershipStatusEnum.ACTIVE

    @staticmethod
    def __parse_datetime(value: object) -> datetime | None:
        if not isinstance(value, str):
            return None
        try:
            return datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            return None

    @staticmethod
    def __get_type_name(
        membership_type_id: object,
        type_names: dict[int, str],
        fallback: object = None,
    ) -> str | None:
        try:
            name = type_names.get(int(membership_type_id))
        except (TypeError, ValueError):
            name = None
        if name is not None:
            return name
        return fallback if isinstance(fallback, str) else None


GetMembershipConfirmationReportUseCaseDep = Annotated[
    GetMembershipConfirmationReportUseCase,
    Depends(GetMembershipConfirmationReportUseCase),
]
