from typing import Annotated

from fastapi import Query
from pydantic import BaseModel

from app.domains.memberships.models import MembershipRequestStatusEnum


class MembershipRequestsFilters(BaseModel):
    status: Annotated[MembershipRequestStatusEnum | None, Query(description="Membership request status filter")] = None
