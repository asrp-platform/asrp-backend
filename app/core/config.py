from os import getenv
from pathlib import Path

from cryptography.fernet import Fernet
from dotenv import load_dotenv
from pydantic import BaseModel
from pydantic_settings import BaseSettings

from app.core.storage.base_storage import S3BaseStorage

load_dotenv()

DEV_MODE: bool = getenv("DEV_MODE", "true").strip().lower() in {"true", "1", "yes"}

# ~\Desktop\asrp-backend
BASE_DIR = Path(__file__).parent.parent.parent

CONVENTION = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}


class GmailConfig(BaseModel):
    GMAIL_USERNAME: str | None = None
    GMAIL_PASSWORD: str | None = None
    GMAIL_FROM: str | None = None
    GMAIL_PORT: int | None = None
    GMAIL_SERVER: str | None = None


class S3Config(BaseModel):
    S3_ACCESS_KEY: str = "minioadmin"
    S3_SECRET_KEY: str = "minioadmin"
    S3_BUCKET: str = "uploads"
    S3_REGION: str = "us-east-1"
    S3_ENDPOINT: str = "http://localhost:9000"
    S3_PUBLIC_URL: str = "http://localhost:9000"


class Settings(BaseSettings, GmailConfig, S3Config):
    DB_HOST: str = "localhost"
    DB_PORT: str = "5432"
    DB_PASSWORD: str = "test"
    DB_USER: str = "test"
    DB_NAME: str = "test"

    SECRET_KEY: str
    ALGORITHM: str
    FERNET_KEY: str

    NAME_CHANGE_REQUEST_COOLDOWN_DAYS: int | None = 14

    ACCESS_TOKEN_LIFESPAN_HOURS: int = 1
    REFRESH_TOKEN_LIFETIME_DAYS: int = 1
    REFRESH_TOKEN_REMEMBER_ME_LIFETIME_DAYS: int = 30

    MEDIA_DIR_NAME: str = "media"
    MEDIA_API_PATH: str = "/api/media"
    MEDIA_STORAGE_PATH: Path = Path("media")
    NEWS_UPLOADS_PATH: Path = MEDIA_STORAGE_PATH / "news_uploads"
    DIRECTORS_BOARD_UPLOADS_PATH: Path = MEDIA_STORAGE_PATH / "directors_board_uploads"
    BYLAWS_PATH: Path = MEDIA_STORAGE_PATH / "bylaws"

    FRONTEND_DOMAIN_HTTP: str
    FRONTEND_DOMAIN: str

    @property
    def fernet_key_bytes(self):
        return self.FERNET_KEY.encode()

    class ConfigDict:
        env: Path = BASE_DIR / ".env"


settings = Settings()

s3_storage = S3BaseStorage(
    access_key=settings.S3_ACCESS_KEY,
    secret_key=settings.S3_SECRET_KEY,
    endpoint_url=settings.S3_ENDPOINT,
    bucket_name=settings.S3_BUCKET,
    region_name=settings.S3_REGION,
)
fernet = Fernet(settings.fernet_key_bytes)

DB_URL: str = f"postgresql+asyncpg://{settings.DB_USER}:{settings.DB_PASSWORD}@{settings.DB_HOST}:{settings.DB_PORT}/{settings.DB_NAME}"
TEST_DB_URL: str = (
    f"postgresql+asyncpg://{settings.DB_USER}:{settings.DB_PASSWORD}@{settings.DB_HOST}:{settings.DB_PORT}/test"
)
