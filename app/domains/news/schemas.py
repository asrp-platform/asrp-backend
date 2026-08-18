from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, HttpUrl, field_serializer

from app.core.database.mixins import UCIMixinSchema
from app.domains.users.schemas import UserPublicSchema


class CreateNewsSchema(BaseModel):
    title: str
    cover_key: str | None
    body: dict
    when: str | None
    where: str | None
    is_published: bool


class UpdateNewsSchema(BaseModel):
    title: str | None = None
    cover_key: str | None = None
    body: dict | None = None
    when: str | None = None
    where: str | None = None
    is_published: bool | None = None


class NewsSchema(CreateNewsSchema, UCIMixinSchema):
    slug: str
    author_id: int
    cover_url: str | None = None

    model_config = ConfigDict(from_attributes=True)


class NewsWithAuthorSchema(NewsSchema):
    author: UserPublicSchema


class WebinarBaseSchema(UCIMixinSchema):
    title: str
    description: str
    learning_objectives: list[str] = Field(
        default_factory=list,
        max_length=10,
    )
    slug: str

    speaker_name: str
    speaker_description: str | None

    join_link: HttpUrl | None
    bunny_video_id: str | None

    starts_at: AwareDatetime
    ends_at: AwareDatetime
    location: str | None = Field(default=None, max_length=255)

    member_only: bool
    archived: bool
    timezone: str
    language: str | None

    model_config = ConfigDict(from_attributes=True)


class UserWebinarSchema(WebinarBaseSchema):
    is_registered: bool


class WebinarPlaybackSchema(BaseModel):
    embed_url: HttpUrl | None


class CreateWebinarSchema(BaseModel):
    title: str = Field(min_length=2)
    description: str
    learning_objectives: list[str] | None = None

    speaker_name: str = Field(min_length=2)
    speaker_description: str | None = Field(default=None, min_length=2)

    join_link: HttpUrl | None = None
    bunny_video_id: str | None = None

    starts_at: AwareDatetime
    location: str | None = Field(default=None, max_length=255)
    timezone: str
    language: str | None = None

    member_only: bool

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "title": "Modern approaches to cardiac surgery",
                    "description": "A practical webinar about current cardiac surgery techniques.",
                    "learning_objectives": [
                        "Review current surgical approaches",
                        "Discuss clinical cases",
                    ],
                    "speaker_name": "Dr. John Smith",
                    "speaker_description": "Cardiac surgeon with 15 years of clinical experience.",
                    "join_link": "https://example.com/webinars/join",
                    "starts_at": "2026-08-15T15:00:00Z",
                    "location": "Online",
                    "member_only": True,
                }
            ]
        }
    )

    @field_serializer("join_link")
    def serialize_urls(self, value: HttpUrl | None) -> str | None:
        return str(value) if value is not None else None


class UpdateWebinarSchema(BaseModel):
    title: str | None = Field(default=None, min_length=2)
    description: str | None = None
    learning_objectives: list[str] | None = Field(default=None, max_length=10)

    speaker_name: str | None = Field(default=None, min_length=2)
    speaker_description: str | None = Field(default=None, min_length=2)

    join_link: HttpUrl | None = None
    bunny_video_id: str | None = None

    starts_at: AwareDatetime | None = None
    location: str | None = Field(default=None, max_length=255)
    member_only: bool | None = None
    archived: bool | None = None
    timezone: str | None = None
    language: str | None = None

    @field_serializer("join_link")
    def serialize_urls(self, value: HttpUrl | None) -> str | None:
        return str(value) if value is not None else None
