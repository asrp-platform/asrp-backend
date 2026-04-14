from typing import Annotated

from fastapi import Depends
from sqlalchemy import select
from sqlalchemy.orm import joinedload

from app.domains.memberships.exceptions import (
    MembershipRequestAlreadyExistsError,
    MembershipRequestNotFoundError,
    MembershipTypeNotFoundError,
)
from app.domains.memberships.infrastructure import MembershipsUnitOfWork, get_memberships_unit_of_work
from app.domains.memberships.models import MembershipRequest, MembershipType, MembershipTypeEnum


class MembershipService:
    def __init__(self, uow: MembershipsUnitOfWork):
        self.uow = uow

    async def get_user_membership_request(self, user_id: int) -> MembershipRequest | None:
        async with self.uow:
            stmt = select(MembershipRequest).options(joinedload(MembershipRequest.membership_type))
            return await self.uow.membership_request_repository.get_first_by_kwargs(stmt=stmt, user_id=user_id)

    async def get_membership_request_by_id(self, membership_request_id: int) -> MembershipRequest:
        membership_request = await self.uow.membership_request_repository.get_first_by_kwargs(id=membership_request_id)
        if membership_request is None:
            raise MembershipRequestNotFoundError("Membership request with provided ID not found")
        return membership_request

    async def get_membership_type(self, membership_type: MembershipTypeEnum) -> MembershipType:
        membership_type = await self.uow.membership_type_repository.get_first_by_kwargs(type=membership_type.value)
        if membership_type is None:
            raise MembershipTypeNotFoundError("Provided membership type not found")
        return membership_type

    async def create_membership_request(self, user_id: int, membership_type: MembershipTypeEnum, **kwargs):
        membership_request = await self.uow.membership_request_repository.get_first_by_kwargs(user_id=user_id)
        if membership_request is not None:
            raise MembershipRequestAlreadyExistsError("Membership for provided User already exists")

        membership_type = await self.uow.membership_type_repository.get_first_by_kwargs(type=membership_type.value)

        return await self.uow.membership_request_repository.create(
            user_id=user_id, membership_type_id=membership_type.id, **kwargs
        )

    async def update_membership_request(self, membership_request_id: int, **kwargs):
        membership_request = await self.uow.membership_request_repository.get_first_by_kwargs(id=membership_request_id)
        if membership_request is None:
            raise MembershipRequestNotFoundError("Membership request with provided ID not found")
        return await self.uow.membership_request_repository.update(membership_request_id, **kwargs)


def get_membership_service(
    uow: Annotated[MembershipsUnitOfWork, Depends(get_memberships_unit_of_work)],
) -> MembershipService:
    return MembershipService(uow)


MembershipServiceDep = Annotated[MembershipService, Depends(get_membership_service)]
