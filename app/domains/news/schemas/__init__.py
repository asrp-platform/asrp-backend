from app.domains.news.schemas.news_schemas import CreateNewsSchema, NewsSchema, NewsWithAuthorSchema, UpdateNewsSchema
from app.domains.news.schemas.webinars_schemas import (
    CreateWebinarSchema,
    UpdateWebinarSchema,
    UserWebinarSchema,
    WebinarBaseSchema,
    WebinarPlaybackSchema,
)


__all__ = [
    "CreateNewsSchema",
    "NewsSchema",
    "NewsWithAuthorSchema",
    "UpdateNewsSchema",
    "CreateWebinarSchema",
    "UpdateWebinarSchema",
    "UserWebinarSchema",
    "WebinarBaseSchema",
    "WebinarPlaybackSchema",
]
