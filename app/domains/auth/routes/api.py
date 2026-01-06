from typing import Annotated

from fastapi import APIRouter, Query
from fastapi_exception_responses import Responses
from starlette.responses import Response

from app.domains.auth.schemas import (
    AccessToken,
    ChangePasswordSchema,
    JWTTokenResponse,
    LoginForm,
    RegisterFormData,
    ResetPasswordSchema,
)
from app.domains.auth.services import AuthServiceDep
from app.domains.shared.deps import (
    CurrentUserDep,
    RefreshTokenDep,
    create_access_token,
    create_refresh_token,
)
from app.domains.users.models import UserSchema
from app.domains.users.services import UserServiceDep

router = APIRouter(tags=["Authentication"], prefix="/auth")


class RegisterResponses(Responses):
    EMAIL_ALREADY_IN_USE = 409, "Provided email is already in use"


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


class LoginResponses(Responses):
    WRONG_CREDENTIALS = 401, "Wrong credentials"


@router.post("/login", summary="User login", responses=LoginResponses.responses)
async def login(
    response: Response,
    login_data: LoginForm,
    user_service: UserServiceDep,
) -> JWTTokenResponse:
    email, password, remember = login_data.model_dump().values()
    user = await user_service.get_user_by_kwargs(email=email)

    if user is None or not user.verify_password(password):
        raise LoginResponses.WRONG_CREDENTIALS

    access_token = create_access_token({"email": user.email})
    refresh_token = create_refresh_token({"email": user.email}, remember_me=remember)

    # Optional adding access_token into Headers
    response.headers["Authorization"] = f"Bearer {access_token}"
    response.set_cookie(key="refresh_token", value=refresh_token, httponly=True)

    return JWTTokenResponse(access_token=access_token, refresh_token=refresh_token)


class RefreshAccessTokenResponses(Responses):
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


class LogoutResponses(Responses):
    INVALID_TOKEN = 401, "Invalid token"


@router.post(
    "/logout",
    responses=LogoutResponses.responses,
)
async def logout(
    response: Response,
    current_user: CurrentUserDep,  # noqa auth dependency
) -> str:
    response.delete_cookie("refresh_token")
    return "Successfully logged out"


@router.post(
    "/password-reset",
    summary="Creates a password reset token",
)
async def reset_password(auth_service: AuthServiceDep, data: ResetPasswordSchema) -> None:
    await auth_service.reset_password(data.email)


class VerifyTokenResponses(Responses):
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


class ConfirmPasswordResetResponses(Responses):
    INVALID_TOKEN = 400, "Invalid token"


@router.post("/password-reset/confirm")
async def confirm_password_reset(
    token: Annotated[str, Query(...)],
    auth_service: AuthServiceDep,
    data: ChangePasswordSchema,
):
    try:
        email = auth_service.verify_password_reset_token(token.encode())
        await auth_service.change_password(email, data.password)
    except ValueError:
        raise ConfirmPasswordResetResponses.INVALID_TOKEN
