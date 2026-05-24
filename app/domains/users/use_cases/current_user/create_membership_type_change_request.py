from typing import Annotated

from fastapi import Depends

from app.core.common.exceptions import ResourceAlreadyExistsError
from app.domains.memberships.exceptions import (
    CantChangeToHonoraryMembershipError,
    InvalidMembershipTypeDowngradeError,
    InvalidMembershipTypeUpgradeError,
    NoMembershipError,
    SameMembershipTypeChangeRequestError,
)
from app.domains.memberships.models import MembershipType, MembershipTypeEnum, UserMembership
from app.domains.memberships.services import (
    MembershipService,
    MembershipServiceDep,
    MembershipTypeChangeService,
    MembershipTypeChangeServiceDep,
    MembershipTypeService,
    MembershipTypeServiceDep,
)
from app.domains.shared.transaction_managers import TransactionManager, TransactionManagerDep


class CreateMembershipTypeChangeRequestUseCase:
    def __init__(
        self,
        transaction_manager: TransactionManager,
        membership_type_change_requests_service: MembershipTypeChangeService,
        membership_service: MembershipService,
        membership_type_service: MembershipTypeService,
    ):
        self.__transaction_manager = transaction_manager
        self.__membership_type_change_requests_service = membership_type_change_requests_service
        self.__membership_service = membership_service
        self.__membership_type_service = membership_type_service

    async def execute(self, current_user_membership: UserMembership, **kwargs):
        upgrade = kwargs.get("upgrade")
        target_membership_type_id = kwargs["target_membership_type_id"]

        if current_user_membership is None:
            raise NoMembershipError("Current user has no membership")

        self._check_target_membership_type_not_the_current(
            target_membership_type_id,
            current_user_membership.membership_type_id,
        )

        async with self.__transaction_manager:
            await self._check_has_no_pending_request(current_user_membership)

            target_membership_type = await self.__membership_type_service.get_membership_type_by_id(
                target_membership_type_id
            )

            self._check_target_membership_type_is_not_honorary(target_membership_type)

            price_difference = await self.__membership_type_service.get_price_difference(
                current_user_membership.membership_type_id,
                target_membership_type.id,
            )

            if upgrade:
                self._check_upgrade_is_correct(price_difference)

                # НЕ создаем запрос на upgrade - создаем его при успешном платеже

                # Создаем Payment с purpose = MEMBERSHIP_TYPE_UPGRADE
                # Создаем CheckoutSession
                # Возвращаем ссылку на платеж

                pass
            else:
                self._check_downgrade_is_correct(price_difference)
                return await self.__membership_type_change_requests_service.create_membership_type_request_service(
                    current_user_membership, **kwargs
                )

    async def _check_has_no_pending_request(self, user_membership: UserMembership):
        pending_request = (
            await self.__membership_type_change_requests_service.get_pending_membership_type_change_request(
                user_membership
            )
        )
        if pending_request is not None:
            raise ResourceAlreadyExistsError("Pending user membership type change request already exists")

    @staticmethod
    def _check_upgrade_is_correct(price_difference: int):
        if price_difference <= 0:
            raise InvalidMembershipTypeUpgradeError(
                "Target membership type is not more expensive than current membership type"
            )

    @staticmethod
    def _check_downgrade_is_correct(price_difference: int):
        if price_difference >= 0:
            raise InvalidMembershipTypeDowngradeError(
                "Target membership type is not cheaper than current membership type"
            )

    @staticmethod
    def _check_target_membership_type_not_the_current(target_id: int, current_id: int):
        if target_id == current_id:
            raise SameMembershipTypeChangeRequestError("Can't change membership type for the same type")

    @staticmethod
    def _check_target_membership_type_is_not_honorary(target_membership_type: MembershipType):
        if target_membership_type.type == MembershipTypeEnum.HONORARY:
            raise CantChangeToHonoraryMembershipError("Can't change membership type to HONORARY")


def get_use_case(
    transaction_manager: TransactionManagerDep,
    membership_type_change_requests_service: MembershipTypeChangeServiceDep,
    membership_service: MembershipServiceDep,
    membership_type_service: MembershipTypeServiceDep,
) -> CreateMembershipTypeChangeRequestUseCase:
    return CreateMembershipTypeChangeRequestUseCase(
        transaction_manager,
        membership_type_change_requests_service,
        membership_service,
        membership_type_service,
    )


CreateMembershipTypeChangeRequestUseCaseDep = Annotated[CreateMembershipTypeChangeRequestUseCase, Depends(get_use_case)]
