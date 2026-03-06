from datetime import datetime, timezone, timedelta
from typing import Annotated, Optional

from fastapi import Depends

from app.domains.memberships.exceptions import MembershipNotFoundError, MembershipTypeNotFoundError
from app.domains.memberships.infrastructure import MembershipsUnitOfWork, get_memberships_unit_of_work
from app.domains.memberships.models import ApprovalStatusEnum, UserMembership


class MembershipsService:
    def __init__(self, uow: MembershipsUnitOfWork):
        self.uow = uow

    async def get_user_membership(self, user_id: int) -> Optional[UserMembership]:
        """Fetch the membership record for a specific user, eagerly loading the membership_type."""
        async with self.uow:
            from sqlalchemy import select
            from sqlalchemy.orm import joinedload
            stmt = select(UserMembership).options(joinedload(UserMembership.membership_type))
            return await self.uow.user_membership_repository.get_first_by_kwargs(stmt=stmt, user_id=user_id)

    async def update_user_membership_mock(
        self,
        user_id: int,
        approval_status: Optional[ApprovalStatusEnum] = None,
        current_period_end: Optional[datetime] = None,
        cancel_at_period_end: Optional[bool] = None,
        auto_renewal: Optional[bool] = True,
        membership_type_id: Optional[int] = None,
    ) -> UserMembership:
        """
        Mock method to update or create a user's membership for testing.
        Automatically extends periods if approvingly.
        """
        async with self.uow:
            membership = await self.uow.user_membership_repository.get_first_by_kwargs(user_id=user_id)
            
            update_data = {}
            if approval_status is not None:
                update_data["approval_status"] = approval_status
                if approval_status == ApprovalStatusEnum.APPROVED and current_period_end is None:
                    if not (membership and membership.current_period_end):
                        update_data["current_period_end"] = datetime.now(tz=timezone.utc) + timedelta(days=365)
            
            if current_period_end is not None:
                update_data["current_period_end"] = current_period_end
            if cancel_at_period_end is not None:
                update_data["cancel_at_period_end"] = cancel_at_period_end
            if auto_renewal is not None:
                update_data["auto_renewal"] = auto_renewal
            
            # If membership_type_id is provided, verify its existence
            if membership_type_id is not None:
                resolved_type = await self.uow.membership_type_repository.get_first_by_kwargs(id=membership_type_id)
                if not resolved_type:
                    raise MembershipTypeNotFoundError(f"Membership type with ID {membership_type_id} does not exist.")
                update_data["membership_type_id"] = membership_type_id

            if membership:
                await self.uow.user_membership_repository.update(membership.id, update_data)
            else:
                # For creating new membership, membership_type_id is required
                if "membership_type_id" not in update_data:
                    # Try to pick first available only if NOT specified (to avoid immediate error if possible),
                    # but if 0 was passed, it already failed above.
                    # Actually, let's be strict: if no ID at all, and no types in DB, error.
                    types, _ = await self.uow.membership_type_repository.list(limit=1)
                    if not types:
                        raise MembershipTypeNotFoundError("No membership types found in the database. Please create a membership type first.")
                    update_data["membership_type_id"] = types[0].id

                if "current_period_end" not in update_data:
                    update_data["current_period_end"] = datetime.now(tz=timezone.utc) + timedelta(days=365)

                new_data = {
                    "user_id": user_id,
                    "approval_status": approval_status or ApprovalStatusEnum.APPROVED,
                    **update_data
                }
                await self.uow.user_membership_repository.create(**new_data)
            
            # Re-fetch with joinedload to ensure response serialization works (outside the update/create logic but inside UoW)
            from sqlalchemy import select
            from sqlalchemy.orm import joinedload
            stmt = select(UserMembership).options(joinedload(UserMembership.membership_type))
            return await self.uow.user_membership_repository.get_first_by_kwargs(stmt=stmt, user_id=user_id)


def get_memberships_service(
    uow: Annotated[MembershipsUnitOfWork, Depends(get_memberships_unit_of_work)]
) -> MembershipsService:
    return MembershipsService(uow)


MembershipsServiceDep = Annotated[MembershipsService, Depends(get_memberships_service)]
