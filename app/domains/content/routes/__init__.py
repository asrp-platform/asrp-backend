from .news_admin_router import router as news_admin_router
from .news_router import router as news_router
from .webinars_admin_router import router as webinars_admin_router
from .webinars_router import router as webinars_router


__all__ = [
    "news_admin_router",
    "news_router",
    "webinars_admin_router",
    "webinars_router",
]
