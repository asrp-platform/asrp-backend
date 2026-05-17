from typing import Annotated

from fastapi import Query
from pydantic import BaseModel

from app.domains.memberships.models import MembershipRequestStatusEnum


class MembershipRequestsFilters(BaseModel):
    user_id: Annotated[int | None, Query(description="Membership request user ID filter")] = None
    status: Annotated[MembershipRequestStatusEnum | None, Query(description="Membership request status filter")] = None


class MembershipTypesFilters(BaseModel):
    is_purchasable: Annotated[bool | None, Query(description="Is membership type purchasable")] = None
