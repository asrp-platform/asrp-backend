from typing import Annotated

from fastapi import APIRouter, Body, Query
from fastapi_exception_responses import Responses as ApiResponses
from starlette.responses import RedirectResponse, Response

from app.core.config import settings
from app.domains.auth.exceptions import (
    EmailAlreadyConfirmedError,
    EmailConfirmationExpiredError,
    RegistrationAlreadyCompletedError,
)
from app.domains.auth.schemas import (
    AccessToken,
    ChangePasswordSchema,
    EmailConfirmationRequestForm,
    JWTTokenResponse,
    LoginForm,
    RegisterFormData,
    ResetPasswordSchema,
)
from app.domains.auth.services import AuthServiceDep, RegisterResponses
from app.domains.shared.deps import (
    RefreshTokenDep,
    create_access_token,
    create_refresh_token,
)
from app.domains.users.exceptions import UserNotFoundError
from app.domains.users.schemas import UserSchema
from app.domains.users.services import UserServiceDep

router = APIRouter(tags=["Authentication"], prefix="/auth")


REFRESH_COOKIE_KWARGS = {
    "key": "refresh_token",
    "path": "/",
    "httponly": True,
    "secure": True,
    "samesite": "none",
}


@router.post(
    "/register",
    summary="User registration",
    responses=RegisterResponses.responses,
    status_code=201,
)
async def register(
    register_form_data: RegisterFormData,
    auth_service: AuthServiceDep,
) -> UserSchema:
    user = await auth_service.register_user(register_form_data)
    return UserSchema.model_validate(user)


class LoginResponses(ApiResponses):
    WRONG_CREDENTIALS = 401, "Wrong credentials"


@router.post("/login", summary="User login", responses=LoginResponses.responses)
async def login(
    response: Response,
    login_data: LoginForm,
    user_service: UserServiceDep,
) -> JWTTokenResponse:
    email, password, remember = login_data.model_dump().values()
    user = await user_service.get_user_by_kwargs(email=email)

    if user is None or not user.verify_password(password) or user.pending is True:
        raise LoginResponses.WRONG_CREDENTIALS

    access_token = create_access_token({"email": user.email})
    refresh_token = create_refresh_token({"email": user.email}, remember_me=remember)
    max_age = (
        settings.refresh_token_cookie_max_age_seconds_remember
        if remember
        else settings.refresh_token_cookie_max_age_seconds
    )

    # Optional adding access_token into Headers
    response.headers["Authorization"] = f"Bearer {access_token}"

    response.set_cookie(
        **REFRESH_COOKIE_KWARGS,
        value=refresh_token,
        max_age=max_age,
    )

    return JWTTokenResponse(access_token=access_token, refresh_token=refresh_token)


class RefreshAccessTokenResponses(ApiResponses):
    NOT_AUTHENTICATED = 401, "Not authenticated"
    INVALID_TOKEN = 401, "Invalid token"


@router.post(
    "/refresh",
    responses=RefreshAccessTokenResponses.responses,
)
async def refresh_access_token(
    response: Response,
    refresh_token_payload: RefreshTokenDep,
) -> AccessToken:
    access_token = create_access_token({"email": refresh_token_payload["email"]})
    response.headers["Authorization"] = f"Bearer {access_token}"
    return AccessToken(access_token=access_token)


class LogoutResponses(ApiResponses):
    INVALID_TOKEN = 401, "Invalid token"


@router.post(
    "/logout",
    responses=LogoutResponses.responses,
)
async def logout(response: Response) -> str:
    response.delete_cookie(**REFRESH_COOKIE_KWARGS)
    return "Successfully logged out"


@router.post(
    "/password-reset",
    summary="Creates a password reset token",
)
async def reset_password(auth_service: AuthServiceDep, data: ResetPasswordSchema) -> None:
    await auth_service.reset_password(data.email)


class VerifyTokenResponses(ApiResponses):
    INVALID_TOKEN = 400, "Invalid token"


@router.get(
    "/password-reset/verify",
    responses=VerifyTokenResponses.responses,
    summary="Verifies password reset token",
)
async def verify_reset_token(
    token: Annotated[str, Query(...)],
    auth_service: AuthServiceDep,
) -> str:
    try:
        return auth_service.verify_password_reset_token(token.encode())
    except ValueError:
        raise VerifyTokenResponses.INVALID_TOKEN


class ConfirmPasswordResetResponses(ApiResponses):
    INVALID_TOKEN = 400, "Invalid token"


@router.post("/password-reset/confirm")
async def confirm_password_reset(
    token: Annotated[str, Query(...)],
    auth_service: AuthServiceDep,
    data: ChangePasswordSchema,
):
    try:
        email = auth_service.verify_password_reset_token(token.encode())
        await auth_service.set_new_password(email, data.password)
    except ValueError:
        raise ConfirmPasswordResetResponses.INVALID_TOKEN


class EmailConfirmRequestResponses(ApiResponses):
    EMAIL_ALREADY_CONFIRMED = (
        409,
        "Provided email is already confirmed",
    )
    USER_NOT_FOUND = (
        404,
        "User with provided email not found",
    )
    CREATED = 201, "Confirmation email sent"


class CompleteRegistrationResponses(ApiResponses):
    REDIRECT = (
        302,
        (
            "Redirects to frontend with one of the following results: "
            "status=success, status=error&reason=expired, status=error&reason=already_registered"
        ),
    )


@router.post(
    "/email-confirmation-requests",
    status_code=201,
    summary="Resend email confirmation link",
    responses=EmailConfirmRequestResponses.responses,
)
async def send_email_confirm_link(
    request_data: Annotated[EmailConfirmationRequestForm, Body(...)], auth_service: AuthServiceDep
):
    try:
        await auth_service.resend_email_confirmation_link(request_data.email)
        return {"detail": "Confirmation email sent"}

    except EmailAlreadyConfirmedError:
        raise EmailConfirmRequestResponses.EMAIL_ALREADY_CONFIRMED

    except UserNotFoundError:
        raise EmailConfirmRequestResponses.USER_NOT_FOUND


@router.get(
    "/email-confirmations",
    summary="Complete registration by email confirmation",
    responses=CompleteRegistrationResponses.responses,
)
async def confirm_email(token: Annotated[str, Query(...)], auth_service: AuthServiceDep):
    try:
        await auth_service.complete_registration(token.encode())
        return RedirectResponse(url=f"{settings.FRONTEND_DOMAIN}/register?status=success", status_code=302)

    except RegistrationAlreadyCompletedError:
        return RedirectResponse(
            url=f"{settings.FRONTEND_DOMAIN}/register?status=error&reason=already_registered", status_code=302
        )

    except EmailConfirmationExpiredError:
        return RedirectResponse(url=f"{settings.FRONTEND_DOMAIN}/register?status=error&reason=expired", status_code=302)
