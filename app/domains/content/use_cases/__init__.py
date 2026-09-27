from app.domains.content.use_cases.case_tags import (
    CreateCaseTagUseCaseDep,
    DeleteCaseTagUseCaseDep,
    GetCaseTagsUseCaseDep,
    GetCaseTagUseCaseDep,
    UpdateCaseTagUseCaseDep,
)
from app.domains.content.use_cases.news import (
    CreateNewsUseCaseDep,
    DeleteNewsUseCaseDep,
    GetNewsByIdUseCaseDep,
    GetNewsListUseCaseDep,
    GetPublishedNewsBySlugUseCaseDep,
    GetPublishedNewsListUseCaseDep,
    UpdateNewsUseCaseDep,
    UploadNewsImageUseCaseDep,
)
from app.domains.content.use_cases.webinars import (
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
    "CreateCaseTagUseCaseDep",
    "DeleteCaseTagUseCaseDep",
    "CreateNewsUseCaseDep",
    "DeleteNewsUseCaseDep",
    "GetNewsByIdUseCaseDep",
    "GetNewsListUseCaseDep",
    "GetPublishedNewsListUseCaseDep",
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
    "GetCaseTagUseCaseDep",
    "GetCaseTagsUseCaseDep",
    "RegisterForWebinarUseCaseDep",
    "UpdateWebinarUseCaseDep",
    "UpdateCaseTagUseCaseDep",
]
