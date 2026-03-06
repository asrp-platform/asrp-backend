from typing import Annotated

from fastapi import Depends
from sqlalchemy import select
from sqlalchemy.orm import joinedload

from app.domains.memberships.infrastructure import MembershipsUnitOfWork, get_memberships_unit_of_work
from app.domains.memberships.models import UserMembership
from app.domains.memberships.use_cases.base import BaseUseCase


class GetUserMembershipUseCase(BaseUseCase[int, UserMembership | None]):
    """
    Use case for fetching a user's membership details.
    """

    def __init__(self, uow: MembershipsUnitOfWork):
        self.uow = uow

    async def execute(self, user_id: int) -> UserMembership | None:
        async with self.uow:
            stmt = select(UserMembership).options(joinedload(UserMembership.membership_type))
            return await self.uow.user_membership_repository.get_first_by_kwargs(stmt=stmt, user_id=user_id)


def get_get_user_membership_use_case(
    uow: Annotated[MembershipsUnitOfWork, Depends(get_memberships_unit_of_work)]
) -> GetUserMembershipUseCase:
    return GetUserMembershipUseCase(uow)


GetUserMembershipUseCaseDep = Annotated[GetUserMembershipUseCase, Depends(get_get_user_membership_use_case)]
