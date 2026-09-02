from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI
from fastapi.exceptions import RequestValidationError
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.middleware.cors import CORSMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

from app.core.common.exceptions import (
    InvalidMimeTypeError,
    NotFoundError,
    NotResourceOwnerError,
    PayloadTooLargeError,
    PermissionDeniedError,
    ResourceAlreadyExistsError,
)
from app.core.config import DEV_MODE, settings
from app.core.database.base_repository import InvalidFilterError, InvalidOrderAttributeError
from app.core.database.setup_db import session_getter
from app.core.logging import configure_logging
from app.core.rate_limiter import rate_limiter_dependency
from app.core.utils.open_api import get_custom_open_api
from app.domains.auth.routes.auth_api import router as auth_router
from app.domains.directors_board.routes.directors_board_admin_api import router as directors_board_admin_router
from app.domains.directors_board.routes.directors_board_api import router as directors_board_router
from app.domains.emails.routes.email_templates_api import router as email_templates_router
from app.domains.feedback.routes.contact_messages_admin_api import router as contact_messages_admin_router
from app.domains.feedback.routes.contact_messages_api import router as contact_messages_router
from app.domains.feedback.routes.feedback_additional_info_admin_api import (
    router as feedback_additional_info_admin_router,
)
from app.domains.feedback.routes.feedback_additional_info_api import router as feedback_additional_info_router
from app.domains.legal_documents.routes.admin_api import router as legal_documents_admin_router
from app.domains.legal_documents.routes.api import router as legal_documents_router
from app.domains.memberships.routes.membership_admin_api import router as membership_admin_router
from app.domains.memberships.routes.membership_requests_admin_api import router as membership_requests_admin_router
from app.domains.memberships.routes.membership_types_admin_api import router as membership_types_admin_router
from app.domains.memberships.routes.membership_types_api import router as membership_types_router
from app.domains.news.routes import (
    news_admin_router,
    news_router,
    webinars_admin_router,
    webinars_router,
)
from app.domains.payments.routes.donations_api import router as donations_router
from app.domains.payments.routes.payments_admin_api import router as payments_admin_router
from app.domains.payments.routes.webhooks import router as webhooks_router
from app.domains.permissions.routes.permissions_admin_api import router as permissions_admin_router
from app.domains.users.routes.admin_api.users_admin_api import router as users_admin_router
from app.domains.users.routes.current_user_api.current_user_api import router as current_user_router
from app.domains.users.routes.current_user_api.current_user_membership_api import (
    router as current_user_membership_router,
)
from app.domains.users.routes.current_user_api.fellowship_api import router as fellowship_router
from app.domains.users.routes.current_user_api.job_api import router as job_router
from app.domains.users.routes.current_user_api.professional_info_api import router as professional_info_router
from app.domains.users.routes.current_user_api.residency_api import router as residency_router
from app.domains.users.routes.members_api.members_api import router as members_router
from app.domains.users.routes.users_api import router as users_router


configure_logging()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # startup
    yield
    # shutdown


app = FastAPI(
    lifespan=lifespan,
    dependencies=[
        Depends(
            rate_limiter_dependency,
            use_cache=False,
        )
    ],
)


@app.exception_handler(NotFoundError)
async def not_found_error_handler(request: Request, exc: NotFoundError):
    return JSONResponse(status_code=404, content={"detail": str(exc)})


@app.exception_handler(NotResourceOwnerError)
async def not_resource_owner_error_handler(request: Request, exc: NotResourceOwnerError):
    return JSONResponse(status_code=403, content={"detail": str(exc)})


@app.exception_handler(ResourceAlreadyExistsError)
async def resource_already_exists_error_handler(request: Request, exc: ResourceAlreadyExistsError):
    return JSONResponse(status_code=409, content={"detail": str(exc)})


@app.exception_handler(PermissionDeniedError)
async def permission_denied_error_handler(request: Request, exc: PermissionDeniedError):
    return JSONResponse(status_code=403, content={"detail": str(exc)})


@app.exception_handler(InvalidOrderAttributeError)
async def invalid_order_attribute_error_handler(request: Request, exc: InvalidOrderAttributeError):
    return JSONResponse(status_code=400, content={"detail": str(exc)})


@app.exception_handler(InvalidFilterError)
async def invalid_filter_error_handler(request: Request, exc: InvalidFilterError):
    return JSONResponse(status_code=400, content={"detail": str(exc)})


@app.exception_handler(InvalidMimeTypeError)
async def invalid_mime_type_error_handler(request: Request, exc: InvalidMimeTypeError) -> JSONResponse:
    return JSONResponse(status_code=415, content={"detail": str(exc) or "Unsupported Media Type"})


@app.exception_handler(PayloadTooLargeError)
async def payload_too_large_error_handler(request: Request, exc: PayloadTooLargeError) -> JSONResponse:
    return JSONResponse(status_code=413, content={"detail": str(exc) or "Payload Too Large"})


# --- Обработчик ошибок 422 ---
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    custom_errors = [
        {"field": ".".join(str(loc) for loc in error["loc"][1:]), "message": error["msg"]} for error in exc.errors()
    ]
    return JSONResponse(
        status_code=422,
        content={"detail": {"errors": custom_errors}},
    )


app.openapi = get_custom_open_api(app)


app.include_router(auth_router, prefix="/api")
app.include_router(current_user_router, prefix="/api")
app.include_router(current_user_membership_router, prefix="/api")
app.include_router(users_router, prefix="/api")
app.include_router(contact_messages_router, prefix="/api")
app.include_router(feedback_additional_info_router, prefix="/api")
app.include_router(directors_board_router, prefix="/api")
app.include_router(legal_documents_router, prefix="/api")
app.include_router(professional_info_router, prefix="/api")
app.include_router(residency_router, prefix="/api")
app.include_router(fellowship_router, prefix="/api")
app.include_router(job_router, prefix="/api")
app.include_router(webhooks_router, prefix="/api")
app.include_router(membership_types_router, prefix="/api")
app.include_router(donations_router, prefix="/api")
app.include_router(webinars_router, prefix="/api")
app.include_router(news_router, prefix="/api")


app.include_router(users_admin_router, prefix="/api/admin")
app.include_router(directors_board_admin_router, prefix="/api/admin")
app.include_router(legal_documents_admin_router, prefix="/api/admin")
app.include_router(permissions_admin_router, prefix="/api/admin")
app.include_router(contact_messages_admin_router, prefix="/api/admin")
app.include_router(feedback_additional_info_admin_router, prefix="/api/admin")
app.include_router(membership_types_admin_router, prefix="/api/admin")
app.include_router(membership_admin_router, prefix="/api/admin")
app.include_router(membership_requests_admin_router, prefix="/api/admin")
app.include_router(payments_admin_router, prefix="/api/admin")
app.include_router(webinars_admin_router, prefix="/api/admin")
app.include_router(news_admin_router, prefix="/api/admin")
app.include_router(email_templates_router, prefix="/api/admin")


app.include_router(members_router, prefix="/api")


if DEV_MODE:
    origins = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:8000",
    ]
else:
    origins = [
        settings.FRONTEND_DOMAIN,
        settings.FRONTEND_DOMAIN_HTTP,
    ]

# Настройка CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,  # Разрешить передачу cookies
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health/live", include_in_schema=True)
async def healthcheck():
    return {"status": "Healthy"}


@app.get("/health/ready", include_in_schema=True)
async def readiness(db: AsyncSession = Depends(session_getter)):  # noqa
    try:
        await db.execute(text("SELECT 1"))
    except Exception:  # noqa
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "database": "unavailable",
            },
        )

    return {
        "status": "ok",
        "database": "ok",
    }
