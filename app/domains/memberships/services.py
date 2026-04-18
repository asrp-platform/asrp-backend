from typing import Annotated, Any

from fastapi import Depends
from sqlalchemy import select
from sqlalchemy.orm import joinedload, selectinload

from app.domains.memberships.exceptions import (
    MembershipRequestAlreadyExistsError,
    MembershipRequestNotFoundError,
    MembershipTypeNotFoundError,
)
from app.domains.memberships.models import MembershipRequest, MembershipType, MembershipTypeEnum
from app.domains.shared.transaction_managers import TransactionManager, TransactionManagerDep
from app.domains.users.exceptions import UserNotFoundError


class MembershipService:
    def __init__(self, transaction_manager: TransactionManager):
        self.transaction_manager = transaction_manager

    async def get_membership_requests_paginated_counted(
        self, limit: int = None, offset: int = None, order_by: str = None, filters: dict[str, Any] = None
    ) -> [list[MembershipRequest], int]:
        stmt = select(MembershipRequest).options(selectinload(MembershipRequest.membership_type))
        async with self.transaction_manager:
            return await self.transaction_manager.membership_requests_repository.list(
                limit, offset, order_by, filters, stmt=stmt
            )

    async def get_user_membership_request(self, user_id: int) -> MembershipRequest | None:
        async with self.transaction_manager:
            user = await self.transaction_manager.user_repository.get_first_by_kwargs(id=user_id)
            if user is None:
                raise UserNotFoundError("User with provided ID not found")
            stmt = select(MembershipRequest).options(joinedload(MembershipRequest.membership_type))
            return await self.transaction_manager.membership_requests_repository.get_first_by_kwargs(
                stmt=stmt, user_id=user_id
            )

    async def get_membership_request_by_id(self, membership_request_id: int) -> MembershipRequest:
        membership_request = await self.transaction_manager.membership_requests_repository.get_first_by_kwargs(
            id=membership_request_id
        )
        if membership_request is None:
            raise MembershipRequestNotFoundError("Membership request with provided ID not found")
        return membership_request

    async def get_membership_type(self, membership_type: MembershipTypeEnum) -> MembershipType:
        membership_type = await self.transaction_manager.membership_type_repository.get_first_by_kwargs(
            type=membership_type.value
        )

        if membership_type is None:
            raise MembershipTypeNotFoundError("Provided membership type not found")
        return membership_type

    async def create_membership_request(self, user_id: int, membership_type: MembershipTypeEnum, **kwargs):
        membership_request = await self.transaction_manager.membership_requests_repository.get_first_by_kwargs(
            user_id=user_id
        )
        if membership_request is not None:
            raise MembershipRequestAlreadyExistsError("Membership for provided User already exists")

        membership_type = await self.transaction_manager.membership_type_repository.get_first_by_kwargs(
            type=membership_type.value
        )

        return await self.transaction_manager.membership_requests_repository.create(
            user_id=user_id, membership_type_id=membership_type.id, **kwargs
        )

    async def update_membership_request(self, membership_request_id: int, **kwargs):
        membership_request = await self.transaction_manager.membership_requests_repository.get_first_by_kwargs(
            id=membership_request_id
        )
        if membership_request is None:
            raise MembershipRequestNotFoundError("Membership request with provided ID not found")
        return await self.transaction_manager.membership_requests_repository.update(membership_request_id, **kwargs)


def get_membership_service(
    transaction_manager: TransactionManagerDep,
) -> MembershipService:
    return MembershipService(transaction_manager)


MembershipServiceDep = Annotated[MembershipService, Depends(get_membership_service)]
