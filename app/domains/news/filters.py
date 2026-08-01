from typing import Annotated

from fastapi import Query
from pydantic import BaseModel


class NewsFilter(BaseModel):
    is_published: Annotated[bool, Query(description="Published filter")] = True
    is_deleted: Annotated[bool, Query(description="Deleted filter")] = False


class WebinarFilters(BaseModel):
    pass
