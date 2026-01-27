from typing import Annotated

from fastapi import Query
from pydantic import BaseModel

from app.domains.feedback.models import ContactMessageTypeEnum


class ContactMessagesFilter(BaseModel):
    email__startswith: Annotated[str | None, Query(description="Email filter")] = None
    name__startswith: Annotated[str | None, Query(description="Name filter")] = None
    type: Annotated[ContactMessageTypeEnum | None, Query(description="Contact message type filter")] = None
