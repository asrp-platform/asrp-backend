from typing import Any

from pydantic import AwareDatetime, Field

from app.core.database.mixins import UCIMixinSchema


class WebinarBaseSchema(UCIMixinSchema):
    title: str
    description: dict[str, Any]
    slug: str

    speaker_name: str
    speaker_description: str | None

    registration_link: str | None
    join_link: str | None
    recording_link: str | None

    starts_at: AwareDatetime
    location: str | None = Field(default=None, max_length=255)

    member_only: bool
