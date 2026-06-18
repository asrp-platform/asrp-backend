from enum import Enum
from os import getenv
from pathlib import Path
from urllib.parse import quote

from cryptography.fernet import Fernet
from dotenv import load_dotenv
from pydantic import AliasChoices, BaseModel, Field
from pydantic_settings import BaseSettings


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


class FileStorageTypeEnum(str, Enum):
    S3_STORAGE = "s3"


class TierLimit(BaseModel):
    capacity: float
    refill_rate: float


class RateLimiterConfig(BaseModel):
    # refill_rate - tokens per second

    RATE_LIMITER_GUEST_LIMITS: TierLimit = TierLimit(capacity=30.0, refill_rate=1.0)
    RATE_LIMITER_AUTHENTICATED_LIMITS: TierLimit = TierLimit(capacity=100.0, refill_rate=2.0)
    RATE_LIMITER_PAID_MEMBER_LIMITS: TierLimit = TierLimit(capacity=200.0, refill_rate=5.0)
    RATE_LIMITER_ADMIN_LIMITS: TierLimit = TierLimit(capacity=500.0, refill_rate=10.0)

    RATE_LIMITER_KEY_TTL: int = 3600


class RedisConfig(BaseModel):
    REDIS_HOST: str
    REDIS_PORT: int
    REDIS_USER: str
    REDIS_USER_PASSWORD: str

    REDIS_DB_NUMBER: int
    REDIS_TEST_DB_NUMBER: int

    REDIS_SOCKET_TIMEOUT: float = 0.5


class GmailConfig(BaseModel):
    GMAIL_USERNAME: str | None = None
    GMAIL_PASSWORD: str | None = None
    GMAIL_FROM: str | None = None
    GMAIL_PORT: int | None = None
    GMAIL_SERVER: str | None = None


class S3Config(BaseModel):
    S3_ACCESS_KEY: str = "minioadmin"
    S3_SECRET_KEY: str = "minioadmin"
    S3_DEFAULT_BUCKET: str = Field(default="uploads", validation_alias=AliasChoices("S3_DEFAULT_BUCKET", "S3_BUCKET"))
    S3_REGION: str = "us-east-1"

    S3_ENDPOINT: str | None = None
    S3_PUBLIC_URL: str | None = None


class Settings(BaseSettings, RateLimiterConfig, RedisConfig, GmailConfig, S3Config):
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

    FILE_STORAGE_TYPE: FileStorageTypeEnum = FileStorageTypeEnum.S3_STORAGE
    FILE_STORAGE_URL_EXPIRES_IN: int = 3600  # sec

    STRIPE_API_KEY: str
    STRIPE_WEBHOOK_SECRET: str

    BACKEND_DOMAIN: str = "http://localhost"

    FRONTEND_DOMAIN_HTTP: str
    FRONTEND_DOMAIN: str

    RABBITMQ_DEFAULT_USER: str
    RABBITMQ_DEFAULT_PASS: str
    RABBITMQ_DEFAULT_VHOST: str
    RABBITMQ_HOST: str = "http://localhost"
    RABBITMQ_PORT: int = 5672

    @property
    def refresh_token_cookie_max_age_seconds(self):
        return self.REFRESH_TOKEN_REMEMBER_ME_LIFETIME_DAYS * 24 * 60 * 60

    @property
    def refresh_token_cookie_max_age_seconds_remember(self):
        return self.REFRESH_TOKEN_LIFETIME_DAYS * 24 * 60 * 60

    @property
    def s3_endpoint_url(self) -> str:
        return self.S3_ENDPOINT or ("http://localhost:9000" if DEV_MODE else "http://minio:9000")

    @property
    def s3_public_url(self) -> str:
        return self.S3_PUBLIC_URL or ("http://localhost:9000" if DEV_MODE else self.BACKEND_DOMAIN)

    @property
    def fernet_key_bytes(self):
        return self.FERNET_KEY.encode()

    @property
    def celery_broker_url(self) -> str:
        vhost = quote(self.RABBITMQ_DEFAULT_VHOST, safe="")
        return (
            f"amqp://{self.RABBITMQ_DEFAULT_USER}:"
            f"{self.RABBITMQ_DEFAULT_PASS}@"
            f"{self.RABBITMQ_HOST}:"
            f"{self.RABBITMQ_PORT}/{vhost}"
        )

    class ConfigDict:
        env: Path = BASE_DIR / ".env"


settings = Settings()
fernet = Fernet(settings.fernet_key_bytes)

DB_URL: str = f"postgresql+asyncpg://{settings.DB_USER}:{settings.DB_PASSWORD}@{settings.DB_HOST}:{settings.DB_PORT}/{settings.DB_NAME}"
TEST_DB_URL: str = (
    f"postgresql+asyncpg://{settings.DB_USER}:{settings.DB_PASSWORD}@{settings.DB_HOST}:{settings.DB_PORT}/test"
)
