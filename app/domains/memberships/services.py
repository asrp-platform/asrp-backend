from typing import Annotated

from fastapi import Depends
from sqlalchemy import select
from sqlalchemy.orm import joinedload

from app.domains.memberships.exceptions import MembershipAlreadyExistsError
from app.domains.memberships.infrastructure import MembershipsUnitOfWork, get_memberships_unit_of_work
from app.domains.memberships.models import MembershipRequest, MembershipTypeEnum


class MembershipService:
    def __init__(self, uow: MembershipsUnitOfWork):
        self.uow = uow

    async def get_user_membership(self, user_id: int) -> MembershipRequest | None:
        async with self.uow:
            stmt = select(MembershipRequest).options(joinedload(MembershipRequest.membership_type))
            return await self.uow.user_membership_repository.get_first_by_kwargs(stmt=stmt, user_id=user_id)

    async def create_user_membership(self, user_id: int, membership_type: MembershipTypeEnum, **kwargs):
        membership = await self.uow.user_membership_repository.get_first_by_kwargs(user_id=user_id)
        if membership is not None:
            raise MembershipAlreadyExistsError("Membership for provided User already exists")

        membership_type = await self.uow.membership_type_repository.get_first_by_kwargs(type=membership_type.value)

        return await self.uow.user_membership_repository.create(
            user_id=user_id, membership_type_id=membership_type.id, **kwargs
        )


def get_membership_service(
    uow: Annotated[MembershipsUnitOfWork, Depends(get_memberships_unit_of_work)],
) -> MembershipService:
    return MembershipService(uow)


MembershipServiceDep = Annotated[MembershipService, Depends(get_membership_service)]
