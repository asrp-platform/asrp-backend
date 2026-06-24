from typing import Annotated

from fastapi import Query
from pydantic import BaseModel

from app.domains.memberships.models import MembershipRequestStatusEnum


class MembershipRequestsFilters(BaseModel):
    user_id: Annotated[int | None, Query(description="Membership request user ID filter")] = None
    status: Annotated[MembershipRequestStatusEnum | None, Query(description="Membership request status filter")] = None


class MembershipTypesFilters(BaseModel):
    is_purchasable: Annotated[bool | None, Query(description="Is membership type purchasable")] = None
    price_usd__lt: Annotated[int | None, Query(description="Is price less than provided value")] = None


class UserMembershipTypeChangeRequestsFilters(BaseModel):
    user_membership_id: Annotated[int | None, Query(description="User membership ID filter")] = None
    target_membership_type_id: Annotated[int | None, Query(description="Target membership type ID filter")] = None
    pending: Annotated[bool | None, Query(description="Pending status filter")] = None
    approved: Annotated[bool | None, Query(description="Approved status filter")] = None
    upgrade: Annotated[bool | None, Query(description="Upgrade or downgrade filter")] = None


class MembersFilters(BaseModel):
    user_id: Annotated[int | None, Query(description="Member ID filter")] = None
