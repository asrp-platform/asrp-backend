from jose import jwt

from app.core.config import settings


def decode_jwt(token: str):
    return jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
