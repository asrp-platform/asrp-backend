from typing import Literal

from app.domains.memberships.services import MembershipDowngradeService
from app.domains.shared.transaction_managers import TransactionManager


class ReviewTypeChangeRequest:
    def __init__(
        self,
        transaction_manager: TransactionManager,
        membership_type_change_service: MembershipDowngradeService,
    ):
        self.__transaction_manager = transaction_manager
        self.__membership_type_change_service = membership_type_change_service

    async def _approve(self, type_change_request_id: int):
        return await self.__membership_type_change_service.approve_membership_type_change(type_change_request_id)

    async def execute(self, type_change_request_id: int, action: Literal["approve", "reject"]):
        async with self.__transaction_manager:
            if action == "approve":
                # делаем approve
                await self._approve(type_change_request_id)
                # меняется
