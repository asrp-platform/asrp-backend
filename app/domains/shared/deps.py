from datetime import datetime, timedelta, timezone
from typing import Annotated

from fastapi import Depends
from fastapi.security import APIKeyCookie, HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from starlette import status
from starlette.exceptions import HTTPException

from app.core.config import settings
from app.domains.permissions.models import Permission
from app.domains.permissions.services import PermissionServiceDep
from app.domains.users.models import User
from app.domains.users.services import UserServiceDep

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
refresh_token_cookie = APIKeyCookie(name="refresh_token", auto_error=False)
access_token_header = HTTPBearer(auto_error=False)


def create_access_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(hours=settings.ACCESS_TOKEN_LIFESPAN_HOURS)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def get_email_by_access_token(access_token: HTTPAuthorizationCredentials):
    """Parses access token and returns decoded email from it"""
    if access_token is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authorized")
    try:
        payload = jwt.decode(access_token.credentials, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    email = payload.get("email")

    if not email:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    return email


def create_refresh_token(data: dict, remember_me: bool = False) -> str:
    data_to_encode = data.copy()
    if remember_me:
        lifetime = timedelta(days=settings.REFRESH_TOKEN_REMEMBER_ME_LIFETIME_DAYS)
    else:
        lifetime = timedelta(days=settings.REFRESH_TOKEN_LIFETIME_DAYS)
    expire = datetime.now(tz=timezone.utc) + lifetime
    data_to_encode.update({"exp": expire})
    refresh_token = jwt.encode(data_to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return refresh_token


async def verify_refresh_token(
    user_service: UserServiceDep, refresh_token: Annotated[str, Depends(refresh_token_cookie)]
) -> dict | None:
    if refresh_token is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authorized")
    try:
        payload = jwt.decode(refresh_token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user = await user_service.get_user_by_kwargs(email=payload["email"])
        if user is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token is invalid")
        return payload
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token is invalid")


async def get_current_user(
    user_service: UserServiceDep,
    access_token: Annotated[HTTPAuthorizationCredentials, Depends(access_token_header)],
) -> User:
    email = get_email_by_access_token(access_token)
    user = await user_service.get_user_by_kwargs(email=email)

    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    return user


async def get_admin_user(
    user_service: UserServiceDep,
    access_token: Annotated[HTTPAuthorizationCredentials, Depends(access_token_header)],
) -> User | None:
    user = await get_current_user(user_service, access_token)
    if not user.admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")
    return user


async def get_users_permissions(
    permission_service: PermissionServiceDep,
    user_service: UserServiceDep,
    access_token: Annotated[HTTPAuthorizationCredentials, Depends(access_token_header)],
):
    user = await get_current_user(user_service, access_token)
    user_permissions = await permission_service.get_user_permissions(user.id)
    return list(map(lambda permissions: permissions.action, user_permissions))


RefreshTokenDep = Annotated[str, Depends(verify_refresh_token)]
CurrentUserDep = Annotated[User, Depends(get_current_user)]
AdminUserDep = Annotated[User, Depends(get_admin_user)]
AdminPermissionsDep = Annotated[list[Permission], Depends(get_users_permissions)]
