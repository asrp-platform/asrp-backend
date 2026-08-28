from typing import Annotated

from fastapi import Depends

from app.core.common.exceptions import NotFoundError
from app.domains.memberships.models import UserMembership
from app.domains.memberships.schemas.user_memberships import MembershipConfirmationSchema
from app.domains.memberships.services import UserMembershipServiceDep
from app.domains.shared.transaction_managers import TransactionManagerDep
from app.domains.users.models import User


class GetMembershipConfirmationUseCase:
    def __init__(self, transaction_manager: TransactionManagerDep, user_membership_service: UserMembershipServiceDep):
        self.__tm = transaction_manager
        self.__user_membership_service = user_membership_service

    async def execute(self, current_user: User) -> MembershipConfirmationSchema:
        async with self.__tm:
            membership = await self.__user_membership_service.get_user_membership_by_user_id(current_user.id)

            if membership is None:
                raise NotFoundError("Membership for the current user not found")

            return MembershipConfirmationSchema(
                member_name=current_user.full_name,
                membership_type=membership.membership_type.name or membership.membership_type.type.value,
                membership_id=format_membership_id(membership),
                valid_through=membership.expires_at,
            )


def format_membership_id(membership: UserMembership) -> str:
    return f"ASRP-{membership.created_at.year}-{membership.id:05d}"


GetMembershipConfirmationUseCaseDep = Annotated[
    GetMembershipConfirmationUseCase, Depends(GetMembershipConfirmationUseCase)
]
