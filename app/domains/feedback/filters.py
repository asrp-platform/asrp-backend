from datetime import date
from typing import Annotated

from fastapi import Query
from pydantic import BaseModel, model_validator
from pydantic_core import PydanticCustomError

from app.domains.feedback.models import ContactMessageTypeEnum


class ContactMessagesFilter(BaseModel):
    email__startswith: Annotated[str | None, Query(description="Email filter")] = None
    name__startswith: Annotated[str | None, Query(description="Name filter")] = None
    type: Annotated[ContactMessageTypeEnum | None, Query(description="Contact message type filter")] = None


class FeedbackDateRangeFilter(BaseModel):
    date_from: Annotated[
        date | None,
        Query(description="Include records created on or after this date (inclusive), format YYYY-MM-DD."),
    ] = None
    date_to: Annotated[
        date | None,
        Query(description="Include records created on or before this date (inclusive), format YYYY-MM-DD."),
    ] = None

    @model_validator(mode="after")
    def validate_date_range(self):
        if self.date_from and self.date_to and self.date_from > self.date_to:
            raise PydanticCustomError("invalid_date_range", "date_from must be less than or equal to date_to")
        return self


class FeedbackInterestsFilter(BaseModel):
    search: Annotated[
        str | None,
        Query(
            description="Case-insensitive substring search in the interest description text.",
        ),
    ] = None
    has_telegram: Annotated[
        bool | None,
        Query(
            description="When true, return only records with non-empty Telegram username; "
            "when false, return only records without Telegram username.",
        ),
    ] = None
