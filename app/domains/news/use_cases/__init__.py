from app.domains.news.use_cases.news import (
    CreateNewsUseCaseDep,
    DeleteNewsUseCaseDep,
    GetNewsByIdUseCaseDep,
    GetNewsListUseCaseDep,
    GetPublishedNewsBySlugUseCaseDep,
    UpdateNewsUseCaseDep,
    UploadNewsImageUseCaseDep,
)
from app.domains.news.use_cases.webinars import (
    CreateWebinarUseCaseDep,
    DeleteWebinarUseCaseDep,
    GetAdminWebinarsUseCaseDep,
    GetRegisteredWebinarUsersUseCaseDep,
    GetWebinarPlaybackUseCaseDep,
    GetWebinarsUseCaseDep,
    GetWebinarUseCaseDep,
    RegisterForWebinarUseCaseDep,
    UpdateWebinarUseCaseDep,
)


__all__ = [
    "CreateNewsUseCaseDep",
    "DeleteNewsUseCaseDep",
    "GetNewsByIdUseCaseDep",
    "GetNewsListUseCaseDep",
    "GetPublishedNewsBySlugUseCaseDep",
    "UpdateNewsUseCaseDep",
    "UploadNewsImageUseCaseDep",
    "CreateWebinarUseCaseDep",
    "DeleteWebinarUseCaseDep",
    "GetAdminWebinarsUseCaseDep",
    "GetRegisteredWebinarUsersUseCaseDep",
    "GetWebinarPlaybackUseCaseDep",
    "GetWebinarUseCaseDep",
    "GetWebinarsUseCaseDep",
    "RegisterForWebinarUseCaseDep",
    "UpdateWebinarUseCaseDep",
]
