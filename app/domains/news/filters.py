from datetime import datetime
from enum import Enum
from typing import Annotated

from fastapi import Query
from pydantic import BaseModel


class NewsFilter(BaseModel):
    title__startswith: Annotated[str | None, Query(description="Title filter")] = None
    when__startswith: Annotated[str | None, Query(description="Event date text filter")] = None
    where__startswith: Annotated[str | None, Query(description="Event location filter")] = None
    is_published: Annotated[bool | None, Query(description="Published filter")] = None
    created_at__gte: Annotated[datetime | None, Query(description="Created_at greater filter")] = None
    created_at__lte: Annotated[datetime | None, Query(description="Created_at less filter")] = None
    updated_at__gte: Annotated[datetime | None, Query(description="Updated_at greater filter")] = None
    updated_at__lte: Annotated[datetime | None, Query(description="Updated_at less filter")] = None


class PublicNewsFilter(BaseModel):
    title__startswith: Annotated[str | None, Query(description="Title filter")] = None
    created_at__gte: Annotated[datetime | None, Query(description="Created_at greater filter")] = None
    created_at__lte: Annotated[datetime | None, Query(description="Created_at less filter")] = None


class WebinarStartFilterEnum(str, Enum):
    UPCOMING = "UPCOMING"
    PAST = "PAST"
    ALL = "ALL"


class WebinarFilters(BaseModel):
    status: Annotated[WebinarStartFilterEnum, Query(description="Webinar status filter")] = WebinarStartFilterEnum.ALL
    archived: Annotated[bool | None, Query(description="Archived filter")] = None
    title__startswith: Annotated[str | None, Query(description="Webinar title filter")] = None
