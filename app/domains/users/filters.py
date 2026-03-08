from typing import Annotated

from fastapi import Query
from pydantic import BaseModel


class UsersFilter(BaseModel):
    pending: Annotated[bool | None, Query(description="Pending filter")] = None
    stuff: Annotated[bool | None, Query(description="Stuff filter")] = None
    email_confirmed: Annotated[bool | None, Query(description="Email confirmed filter")] = None
    email__startswith: Annotated[str | None, Query(description="Email filter")] = None
    firstname__startswith: Annotated[str | None, Query(description="Firstname startswith")] = None
    lastname__startswith: Annotated[str | None, Query(description="Lastname startswith")] = None
