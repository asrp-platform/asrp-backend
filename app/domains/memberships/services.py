from typing import Annotated, Any

from fastapi import Depends
from sqlalchemy import select
from sqlalchemy.orm import aliased, selectinload

from app.core.common.exceptions import NotFoundError, ResourceAlreadyExistsError
from app.domains.memberships.models import (
    MembershipDowngradeRequest,
    MembershipRequest,
    MembershipType,
    MembershipTypeEnum,
    UserMembership,
)
from app.domains.shared.transaction_managers import TransactionManager, TransactionManagerDep
from app.domains.users.models import User


class MembershipService:
    def __init__(self, transaction_manager: TransactionManager):
        self.__transaction_manager = transaction_manager

    async def get_membership_requests_paginated_counted(
        self, limit: int = None, offset: int = None, order_by: str = None, filters: dict[str, Any] = None
    ) -> [list[MembershipRequest], int]:
        stmt = select(MembershipRequest).options(
            selectinload(MembershipRequest.membership_type),
            selectinload(MembershipRequest.user),
        )
        async with self.__transaction_manager:
            return await self.__transaction_manager.membership_requests_repository.list(
                limit, offset, order_by, filters, stmt=stmt
            )

    async def get_user_membership_request(self, user_id: int) -> MembershipRequest | None:
        async with self.__transaction_manager:
            user = await self.__transaction_manager.user_repository.get_first_by_kwargs(id=user_id)
            if user is None:
                raise NotFoundError("User with provided ID not found")
            stmt = select(MembershipRequest).options(
                selectinload(MembershipRequest.membership_type),
                selectinload(MembershipRequest.user),
            )
            return await self.__transaction_manager.membership_requests_repository.get_first_by_kwargs(
                stmt=stmt, user_id=user_id
            )

    async def get_membership_request_by_id(self, membership_request_id: int) -> MembershipRequest:
        stmt = select(MembershipRequest).options(selectinload(MembershipRequest.membership_type))
        membership_request = await self.__transaction_manager.membership_requests_repository.get_first_by_kwargs(
            stmt=stmt,
            id=membership_request_id,
        )
        if membership_request is None:
            raise NotFoundError("Membership request with provided ID not found")
        return membership_request

    async def create_membership_request(self, user_id: int, membership_type: MembershipTypeEnum, **kwargs):
        membership_request = await self.__transaction_manager.membership_requests_repository.get_first_by_kwargs(
            user_id=user_id
        )
        if membership_request is not None:
            raise ResourceAlreadyExistsError("Membership for provided User already exists")

        membership_type = await self.__transaction_manager.membership_type_repository.get_first_by_kwargs(
            type=membership_type.value
        )

        return await self.__transaction_manager.membership_requests_repository.create(
            user_id=user_id, membership_type_id=membership_type.id, **kwargs
        )

    async def update_membership_request(self, membership_request_id: int, **kwargs):
        membership_request = await self.__transaction_manager.membership_requests_repository.get_first_by_kwargs(
            id=membership_request_id
        )
        if membership_request is None:
            raise NotFoundError("Membership request with provided ID not found")
        return await self.__transaction_manager.membership_requests_repository.update(membership_request_id, **kwargs)


class MembershipTypeService:
    def __init__(self, transaction_manager: TransactionManager):
        self.__transaction_manager = transaction_manager

    async def get_membership_types(
        self, limit: int = None, offset: int = None, order_by: str = None, filters: dict[str, Any] = None
    ) -> list[MembershipType]:
        # Called at endpoint
        async with self.__transaction_manager:
            membership_types, _ = await self.__transaction_manager.membership_type_repository.list(
                limit, offset, order_by, filters
            )
            return membership_types

    async def get_price_difference(self, current_type_id, target_type_id) -> int:
        current = aliased(MembershipType)
        target = aliased(MembershipType)
        stmt = (
            select((target.price_usd - current.price_usd).label("price_diff"))
            .where(current.id == current_type_id)
            .where(target.id == target_type_id)
        )
        return (await self.__transaction_manager._session.execute(stmt)).scalar_one()

    async def get_membership_type_by_id(self, membership_type_id: int) -> MembershipType:
        membership_type = await self.__transaction_manager.membership_type_repository.get_first_by_kwargs(
            id=membership_type_id
        )
        if membership_type is None:
            raise NotFoundError("Provided membership type not found")
        return membership_type

    async def get_membership_type_by_value(self, membership_type: MembershipTypeEnum) -> MembershipType:
        membership_type = await self.__transaction_manager.membership_type_repository.get_first_by_kwargs(
            type=membership_type.value
        )

        if membership_type is None:
            raise NotFoundError("Provided membership type not found")
        return membership_type


class UserMembershipService:
    def __init__(self, transaction_manager: TransactionManager):
        self.__transaction_manager = transaction_manager

    async def create_user_membership(self, user_id: int, **kwargs) -> UserMembership:
        user_membership = await self.__transaction_manager.user_membership_repository.get_first_by_kwargs(
            user_id=user_id
        )
        if user_membership is not None:
            raise ResourceAlreadyExistsError(f"User membership already exists for the user with ID={user_id}")
        return await self.__transaction_manager.user_membership_repository.create(user_id=user_id, **kwargs)

    async def get_user_membership_by_user_id(self, user_id: int) -> UserMembership | None:
        async with self.__transaction_manager:
            stmt = select(UserMembership).options(selectinload(UserMembership.membership_type))
            user = await self.__transaction_manager.user_repository.get_first_by_kwargs(id=user_id)

            if user is None:
                raise NotFoundError("User with provided ID not found")

            return await self.__transaction_manager.user_membership_repository.get_first_by_kwargs(
                stmt=stmt,
                user_id=user_id,
            )


class MembershipDowngradeService:
    def __init__(self, transaction_manager: TransactionManager):
        self.__transaction_manager = transaction_manager

    async def create_downgrade_request(self, user_membership: UserMembership, **kwargs):
        return await self.__transaction_manager.membership_downgrade_requests_repository.create(
            user_membership_id=user_membership.id, **kwargs
        )

    async def get_all_paginated_counted(
        self, limit: int = None, offset: int = None, order_by: str = None, filters: dict[str, Any] = None
    ) -> [list[MembershipDowngradeRequest], int]:
        stmt = select(MembershipDowngradeRequest).options(
            selectinload(MembershipDowngradeRequest.target_membership_type).load_only(
                MembershipType.id, MembershipType.name, MembershipType.type
            ),
            selectinload(MembershipDowngradeRequest.user_membership)
            .selectinload(UserMembership.membership_type)
            .load_only(MembershipType.id, MembershipType.name, MembershipType.type),
            selectinload(MembershipDowngradeRequest.user_membership)
            .selectinload(UserMembership.user)
            .load_only(
                User.id,
                User.email,
            ),
        )
        return await self.__transaction_manager.membership_downgrade_requests_repository.list(
            limit, offset, order_by, filters, stmt=stmt
        )

    async def get_pending_downgrade_request_by_membership(
        self,
        user_membership: UserMembership,
    ) -> MembershipDowngradeRequest | None:
        return await self.__transaction_manager.membership_downgrade_requests_repository.get_first_by_kwargs(
            pending=True, user_membership_id=user_membership.id
        )

    async def get_current_user_membership_type_change_request(
        self,
        user_membership: UserMembership,
    ) -> MembershipDowngradeRequest | None:
        stmt = select(MembershipDowngradeRequest).options(
            selectinload(MembershipDowngradeRequest.target_membership_type).load_only(
                MembershipType.id, MembershipType.name, MembershipType.type
            ),
            selectinload(MembershipDowngradeRequest.user_membership)
            .selectinload(UserMembership.membership_type)
            .load_only(MembershipType.id, MembershipType.name, MembershipType.type),
        )
        return await self.__transaction_manager.membership_downgrade_requests_repository.get_first_by_kwargs(
            stmt=stmt,
            user_membership_id=user_membership.id,
            pending=True,
        )

    async def approve_membership_type_change(self, type_change_request_id: int) -> MembershipDowngradeRequest:
        downgrade_request: MembershipDowngradeRequest = (
            await self.__transaction_manager.membership_downgrade_requests_repository.update(
                type_change_request_id, approved=True, pending=False
            )
        )
        await self.__transaction_manager.user_membership_repository.update(
            downgrade_request.user_membership_id, membership_type_id=downgrade_request.target_membership_type_id
        )
        return downgrade_request

    async def reject_membership_type_change(self, type_change_request_id: int, admin_comment: str):
        type_change_request = (
            await self.__transaction_manager.membership_downgrade_requests_repository.get_first_by_kwargs(
                id=type_change_request_id
            )
        )
        if type_change_request is None:
            raise NotFoundError("Membership type change request with provided ID not found")

        await self.__transaction_manager.membership_downgrade_requests_repository.update(
            type_change_request_id, approved=False, admin_comment=admin_comment, pending=False
        )


def get_membership_service(
    transaction_manager: TransactionManagerDep,
) -> MembershipService:
    return MembershipService(transaction_manager)


def get_user_membership_service(
    transaction_manager: TransactionManagerDep,
) -> UserMembershipService:
    return UserMembershipService(transaction_manager)


def get_membership_type_service(
    transaction_manager: TransactionManagerDep,
) -> MembershipTypeService:
    return MembershipTypeService(transaction_manager)


def get_membership_type_change_request_service(
    transaction_manager: TransactionManagerDep,
) -> MembershipDowngradeService:
    return MembershipDowngradeService(transaction_manager)


MembershipServiceDep = Annotated[MembershipService, Depends(get_membership_service)]
UserMembershipServiceDep = Annotated[UserMembershipService, Depends(get_user_membership_service)]
MembershipTypeServiceDep = Annotated[MembershipTypeService, Depends(get_membership_type_service)]
MembershipTypeChangeServiceDep = Annotated[
    MembershipDowngradeService, Depends(get_membership_type_change_request_service)
]
