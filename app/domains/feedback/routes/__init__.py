from app.domains.feedback.routes.contact_messages_admin_api import router as contact_messages_admin_router
from app.domains.feedback.routes.contact_messages_api import router as contact_messages_router
from app.domains.feedback.routes.feedback_additional_info_admin_api import (
    router as feedback_additional_info_admin_router,
)
from app.domains.feedback.routes.feedback_additional_info_api import router as feedback_additional_info_router


__all__ = [
    "contact_messages_admin_router",
    "contact_messages_router",
    "feedback_additional_info_admin_router",
    "feedback_additional_info_router",
]
