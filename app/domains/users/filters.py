from typing import Annotated

from fastapi import Query
from pydantic import BaseModel

from app.domains.users.models import NameChangeRequestStatusEnum


class UsersFilter(BaseModel):
    pending: Annotated[bool | None, Query(description="Pending filter")] = None
    admin: Annotated[bool | None, Query(description="Admin filter")] = None
    email_confirmed: Annotated[bool | None, Query(description="Email confirmed filter")] = None
    email__startswith: Annotated[str | None, Query(description="Email filter")] = None
    firstname__startswith: Annotated[str | None, Query(description="Firstname startswith")] = None
    lastname__startswith: Annotated[str | None, Query(description="Lastname startswith")] = None


class NameChangeRequestsFilters(BaseModel):
    status: Annotated[NameChangeRequestStatusEnum | None, Query(description="Status filter")] = None
