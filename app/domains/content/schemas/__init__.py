from app.domains.content.schemas.case_tags_schemas import CaseTagSchema, CreateCaseTagSchema, UpdateCaseTagSchema
from app.domains.content.schemas.news_schemas import (
    CreateNewsSchema,
    NewsSchema,
    NewsWithAuthorSchema,
    UpdateNewsSchema,
)
from app.domains.content.schemas.webinars_schemas import (
    CreateWebinarSchema,
    UpdateWebinarSchema,
    UserWebinarSchema,
    WebinarBaseSchema,
    WebinarPlaybackSchema,
)


__all__ = [
    "CaseTagSchema",
    "CreateCaseTagSchema",
    "CreateNewsSchema",
    "NewsSchema",
    "NewsWithAuthorSchema",
    "UpdateCaseTagSchema",
    "UpdateNewsSchema",
    "CreateWebinarSchema",
    "UpdateWebinarSchema",
    "UserWebinarSchema",
    "WebinarBaseSchema",
    "WebinarPlaybackSchema",
]
