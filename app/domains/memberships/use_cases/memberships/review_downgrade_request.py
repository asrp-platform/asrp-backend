from typing import Annotated, Literal

from fastapi import Depends

from app.core.utils.permissions import check_permissions
from app.domains.memberships.services import MembershipDowngradeService, MembershipTypeChangeServiceDep
from app.domains.shared.transaction_managers import TransactionManager, TransactionManagerDep


class ReviewMembershipDowngradeRequestUseCase:
    def __init__(
        self,
        transaction_manager: TransactionManager,
        membership_type_change_service: MembershipDowngradeService,
    ):
        self.__transaction_manager = transaction_manager
        self.__membership_type_change_service = membership_type_change_service

    async def execute(
        self,
        downgrade_request_id: int,
        permissions: list[str],
        action: Literal["approve", "reject"],
        admin_comment: str | None,
    ):
        async with self.__transaction_manager:
            check_permissions("memberships.update", permissions)

            if action == "approve":
                return await self.__membership_type_change_service.approve_membership_type_change(downgrade_request_id)
            if action == "reject":
                return await self.__membership_type_change_service.reject_membership_type_change(
                    downgrade_request_id, admin_comment
                )


def get_use_case(
    transaction_manager: TransactionManagerDep,
    membership_type_change_service: MembershipTypeChangeServiceDep,
) -> ReviewMembershipDowngradeRequestUseCase:
    return ReviewMembershipDowngradeRequestUseCase(transaction_manager, membership_type_change_service)


ReviewMembershipDowngradeRequestUseCaseDep = Annotated[ReviewMembershipDowngradeRequestUseCase, Depends(get_use_case)]
