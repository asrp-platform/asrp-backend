from enum import Enum
from typing import Annotated

from fastapi import Query
from pydantic import BaseModel


class NewsFilter(BaseModel):
    is_published: Annotated[bool, Query(description="Published filter")] = True
    is_deleted: Annotated[bool, Query(description="Deleted filter")] = False


class WebinarStartFilterEnum(str, Enum):
    UPCOMING = "UPCOMING"
    PAST = "PAST"
    ALL = "ALL"


class WebinarFilters(BaseModel):
    status: Annotated[WebinarStartFilterEnum, Query(description="Webinar status filter")] = WebinarStartFilterEnum.ALL
    archived: Annotated[bool | None, Query(description="Archived filter")] = None
    title__startswith: Annotated[str | None, Query(description="Webinar title filter")] = None
