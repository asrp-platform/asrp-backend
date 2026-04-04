from dataclasses import dataclass, field
from datetime import datetime
from typing import Annotated

from fastapi import Depends
from sqlalchemy import select
from sqlalchemy.orm import joinedload

from app.core.common.base_use_case import BaseUseCase
from app.domains.memberships.exceptions import MembershipTypeNotFoundError
from app.domains.memberships.infrastructure import MembershipsUnitOfWork, get_memberships_unit_of_work
from app.domains.memberships.models import MembershipRequest, MembershipRequestStatusEnum, MembershipTypeEnum


@dataclass
class UpdateUserMembershipMockRequest:
    user_id: int
    status: MembershipRequestStatusEnum = MembershipRequestStatusEnum.SUBMITTED
    current_period_end: datetime | None = None
    auto_renewal: bool = True
    membership_type: MembershipTypeEnum = MembershipTypeEnum.ACTIVE
    updated_fields: set[str] = field(default_factory=set)


class UpdateUserMembershipMockUseCase(BaseUseCase[UpdateUserMembershipMockRequest, MembershipRequest]):
    """
    Use case for updating or creating a user's membership for testing/mocking.
    """

    def __init__(self, uow: MembershipsUnitOfWork):
        self.uow = uow

    async def execute(self, request: UpdateUserMembershipMockRequest) -> MembershipRequest:
        async with self.uow:
            membership = await self.uow.user_membership_repository.get_first_by_kwargs(user_id=request.user_id)

            update_data = await self._build_update_data(request)

            if membership:
                if update_data:
                    await self.uow.user_membership_repository.update(membership.id, **update_data)
            else:
                new_data = await self._build_create_data(request)
                new_data.update(
                    {
                        "user_id": request.user_id,
                    }
                )
                await self.uow.user_membership_repository.create(**new_data)
                await self.uow.user_membership_repository.session.flush()

            # Re-fetch with joinedload to ensure response serialization works
            stmt = select(MembershipRequest).options(joinedload(MembershipRequest.membership_type))
            return await self.uow.user_membership_repository.get_first_by_kwargs(stmt=stmt, user_id=request.user_id)

    async def _build_update_data(self, request: UpdateUserMembershipMockRequest) -> dict:
        update_data = {}

        if "approval_status" in request.updated_fields:
            update_data["approval_status"] = request.approval_status
        if "current_period_end" in request.updated_fields:
            update_data["current_period_end"] = request.current_period_end
        if "auto_renewal" in request.updated_fields:
            update_data["auto_renewal"] = request.auto_renewal
        if "membership_type" in request.updated_fields:
            update_data["membership_type_id"] = await self._get_membership_type_id(request.membership_type)

        return update_data

    async def _build_create_data(self, request: UpdateUserMembershipMockRequest) -> dict:
        membership_type = request.membership_type
        if "membership_type" not in request.updated_fields:
            membership_type = MembershipTypeEnum.ACTIVE

        return {
            "status": request.status if "status" in request.updated_fields else MembershipRequestStatusEnum.SUBMITTED,
            "current_period_end": request.current_period_end
            if "current_period_end" in request.updated_fields
            else None,
            "auto_renewal": request.auto_renewal if "auto_renewal" in request.updated_fields else True,
            "membership_type_id": await self._get_membership_type_id(membership_type),
        }

    async def _get_membership_type_id(self, membership_type: MembershipTypeEnum) -> int:
        resolved_type = await self.uow.membership_type_repository.get_first_by_kwargs(type=membership_type)
        if resolved_type is None:
            raise MembershipTypeNotFoundError(f"Membership type with enum {membership_type.value} does not exist.")
        return resolved_type.id


def get_update_user_membership_mock_use_case(
    uow: Annotated[MembershipsUnitOfWork, Depends(get_memberships_unit_of_work)],
) -> UpdateUserMembershipMockUseCase:
    return UpdateUserMembershipMockUseCase(uow)


UpdateUserMembershipMockUseCaseDep = Annotated[
    UpdateUserMembershipMockUseCase, Depends(get_update_user_membership_mock_use_case)
]
