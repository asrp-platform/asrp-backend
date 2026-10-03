from typing import Annotated

from fastapi import APIRouter, Query
from fastapi_exception_responses import Responses as ApiResponses
from starlette.responses import Response

from app.core.common.exceptions import NotFoundError, ResourceAlreadyExistsError
from app.domains.auth.cookies import REFRESH_TOKEN_COOKIE_KWARGS
from app.domains.auth.exceptions import (
    EmailAlreadyConfirmedError,
    EmailConfirmationExpiredError,
    InvalidCredentialsError,
    RegistrationAlreadyCompletedError,
    UserBannedError,
)
from app.domains.auth.schemas import (
    AccessToken,
    ChangePasswordSchema,
    EmailConfirmationRequestForm,
    JWTTokenResponse,
    LoginForm,
    MessageResponse,
    RegisterFormData,
    ResetPasswordSchema,
)
from app.domains.auth.services import AuthJwtServiceDep, AuthTokenServiceDep
from app.domains.auth.use_cases.complete_registration import CompleteRegistrationUseCaseDep
from app.domains.auth.use_cases.confirm_password_reset import ConfirmPasswordResetUseCaseDep
from app.domains.auth.use_cases.login_user import LoginUserUseCaseDep
from app.domains.auth.use_cases.register_user import RegisterUserUseCaseDep
from app.domains.auth.use_cases.request_password_reset import RequestPasswordResetUseCaseDep
from app.domains.auth.use_cases.resend_email_confirmation import ResendEmailConfirmationUseCaseDep
from app.domains.auth.utils import get_countries
from app.domains.shared.deps import (
    RefreshTokenDep,
)
from app.domains.users.schemas import UserPrivateSchema


router = APIRouter(tags=["Authentication"], prefix="/auth")


class RegisterResponses(ApiResponses):
    EMAIL_ALREADY_IN_USE = 409, "Provided email is already in use"


@router.post(
    "/register",
    summary="User registration",
    responses=RegisterResponses.responses,
    status_code=201,
)
async def register(
    register_form_data: RegisterFormData,
    use_case: RegisterUserUseCaseDep,
) -> UserPrivateSchema:
    try:
        return await use_case.execute(register_form_data)
    except ResourceAlreadyExistsError:
        raise RegisterResponses.EMAIL_ALREADY_IN_USE


class LoginResponses(ApiResponses):
    WRONG_CREDENTIALS = 401, "Wrong credentials"
    USER_BANNED = 403, "User is banned"


@router.post("/login", summary="User login", responses=LoginResponses.responses, status_code=200)
async def login(
    response: Response,
    login_data: LoginForm,
    use_case: LoginUserUseCaseDep,
) -> JWTTokenResponse:
    try:
        result = await use_case.execute(login_data)
    except InvalidCredentialsError:
        raise LoginResponses.WRONG_CREDENTIALS
    except UserBannedError as exc:
        raise LoginResponses.USER_BANNED from exc

    # Optional adding access_token into Headers
    response.headers["Authorization"] = f"Bearer {result.access_token}"

    response.set_cookie(
        **REFRESH_TOKEN_COOKIE_KWARGS,
        value=result.refresh_token,
        max_age=result.refresh_token_max_age,
    )

    return JWTTokenResponse(access_token=result.access_token, refresh_token=result.refresh_token)


class RefreshAccessTokenResponses(ApiResponses):
    NOT_AUTHENTICATED = 401, "Not authenticated"
    INVALID_TOKEN = 401, "Invalid token"


@router.post(
    "/refresh",
    summary="Refresh access token",
    responses=RefreshAccessTokenResponses.responses,
    status_code=200,
)
async def refresh_access_token(
    response: Response,
    refresh_token_payload: RefreshTokenDep,
    jwt_service: AuthJwtServiceDep,
) -> AccessToken:
    access_token = jwt_service.create_access_token({"email": refresh_token_payload["email"]})
    response.headers["Authorization"] = f"Bearer {access_token}"
    return AccessToken(access_token=access_token)


class LogoutResponses(ApiResponses):
    INVALID_TOKEN = 401, "Invalid token"


@router.post(
    "/logout",
    summary="Log out the current session",
    responses=LogoutResponses.responses,
    status_code=200,
)
async def logout(response: Response) -> str:
    response.delete_cookie(**REFRESH_TOKEN_COOKIE_KWARGS)
    return "Successfully logged out"


class PasswordResetRequestResponses(ApiResponses):
    REQUEST_ACCEPTED = 202, "Password reset instructions accepted"


@router.post(
    "/password-reset",
    summary="Request a password reset email",
    responses=PasswordResetRequestResponses.responses,
    status_code=202,
)
async def reset_password(use_case: RequestPasswordResetUseCaseDep, data: ResetPasswordSchema) -> None:
    await use_case.execute(data.email)


class VerifyTokenResponses(ApiResponses):
    INVALID_TOKEN = 400, "Invalid token"


@router.get(
    "/password-reset/verify",
    responses=VerifyTokenResponses.responses,
    summary="Verifies password reset token",
)
async def verify_reset_token(
    token: Annotated[str, Query(...)],
    token_service: AuthTokenServiceDep,
) -> str:
    try:
        return token_service.verify_password_reset_token(token.encode())
    except ValueError:
        raise VerifyTokenResponses.INVALID_TOKEN


class ConfirmPasswordResetResponses(ApiResponses):
    INVALID_TOKEN = 400, "Invalid token"


@router.post(
    "/password-reset/confirm",
    summary="Set a new password using a reset token",
    responses=ConfirmPasswordResetResponses.responses,
    status_code=204,
)
async def confirm_password_reset(
    token: Annotated[str, Query(...)],
    use_case: ConfirmPasswordResetUseCaseDep,
    data: ChangePasswordSchema,
):
    try:
        await use_case.execute(token.encode(), data.password)
    except ValueError:
        raise ConfirmPasswordResetResponses.INVALID_TOKEN


class EmailConfirmRequestResponses(ApiResponses):
    USER_NOT_FOUND = 404, "User with provided email not found"
    EMAIL_ALREADY_CONFIRMED = 409, "Provided email is already confirmed"
    CONFIRMATION_LINK_SENT = 201, "Confirmation email sent"


@router.post(
    "/email-confirmation-requests",
    status_code=201,
    summary="Resend email confirmation link",
    responses=EmailConfirmRequestResponses.responses,
)
async def send_email_confirm_link(
    request_data: EmailConfirmationRequestForm, use_case: ResendEmailConfirmationUseCaseDep
) -> MessageResponse:
    try:
        await use_case.execute(request_data.email)
        return MessageResponse(detail="Confirmation email sent")

    except NotFoundError:
        raise EmailConfirmRequestResponses.USER_NOT_FOUND
    except EmailAlreadyConfirmedError:
        raise EmailConfirmRequestResponses.EMAIL_ALREADY_CONFIRMED


class CompleteRegistrationResponses(ApiResponses):
    SUCCESS = 200, "Email successfully confirmed"
    ALREADY_REGISTERED = 409, "Registration already completed"
    EXPIRED = 401, "Invalid or expired token"


@router.get(
    "/email-confirmations",
    summary="Complete registration by email confirmation",
    responses=CompleteRegistrationResponses.responses,
)
async def confirm_email(token: Annotated[str, Query(...)], use_case: CompleteRegistrationUseCaseDep):
    try:
        await use_case.execute(token.encode())
        return {"detail": "Email successfully confirmed"}

    except RegistrationAlreadyCompletedError:
        raise CompleteRegistrationResponses.ALREADY_REGISTERED

    except EmailConfirmationExpiredError:
        raise CompleteRegistrationResponses.EXPIRED


@router.get(
    "/countries",
    summary="List available countries",
    status_code=200,
)
async def countries_list():
    return get_countries()
