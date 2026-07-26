from typing import Annotated

from fastapi import Query
from pydantic import BaseModel

from app.domains.memberships.models import MembershipTypeEnum
from app.domains.users.models import NameChangeRequestStatusEnum


class UsersFilter(BaseModel):
    pending: Annotated[bool | None, Query(description="Pending filter")] = None
    admin: Annotated[bool | None, Query(description="Admin filter")] = None
    email__startswith: Annotated[str | None, Query(description="Email filter")] = None
    firstname__startswith: Annotated[str | None, Query(description="Firstname startswith")] = None
    lastname__startswith: Annotated[str | None, Query(description="Lastname startswith")] = None


class NameChangeRequestsFilters(BaseModel):
    status: Annotated[NameChangeRequestStatusEnum | None, Query(description="Status filter")] = None


class MembersFilter(BaseModel):
    search: Annotated[str | None, Query(min_length=1, max_length=100, description="Search by member name")] = None
    country: Annotated[str | None, Query(description="Exact country filter")] = None
    state__startswith: Annotated[str | None, Query(description="Exact state filter")] = None
    membership_type: Annotated[MembershipTypeEnum | None, Query(description="Membership type filter")] = None
