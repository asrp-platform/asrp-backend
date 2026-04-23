from loguru import logger

from app.core.config import BASE_DIR, DEV_MODE

LOG_DIR = BASE_DIR / "logs"

REQUEST_LOG_DIR = LOG_DIR / "requests"
AUDIT_LOG_DIR = LOG_DIR / "audit"
ERROR_LOG_DIR = LOG_DIR / "errors"
PAYMENTS_LOG_DIR = LOG_DIR / "payments"
STRIPE_LOG_DIR = PAYMENTS_LOG_DIR / "stripe"

REQUESTS_CHANNEL = "requests"
PRIVILEGES_CHANNEL = "privileges"
PAYMENTS_CHANNEL = "payments"
STRIPE_CHANNEL = "stripe"


def configure_logging() -> None:
    logger.remove()

    REQUEST_LOG_DIR.mkdir(parents=True, exist_ok=True)
    AUDIT_LOG_DIR.mkdir(parents=True, exist_ok=True)
    ERROR_LOG_DIR.mkdir(parents=True, exist_ok=True)
    PAYMENTS_LOG_DIR.mkdir(parents=True, exist_ok=True)
    STRIPE_LOG_DIR.mkdir(parents=True, exist_ok=True)

    logger.add(
        REQUEST_LOG_DIR / "requests.log",
        level="INFO",
        rotation="1 day",
        retention="30 days",
        compression="zip",
        encoding="utf-8",
        enqueue=True,
        filter=lambda record: record["extra"].get("channel") == REQUESTS_CHANNEL,
        format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level} | {message}",
    )

    logger.add(
        AUDIT_LOG_DIR / "privileges.log",
        level="INFO",
        rotation="1 month",
        retention="1 year",
        compression="zip",
        encoding="utf-8",
        enqueue=True,
        filter=lambda record: record["extra"].get("channel") == PRIVILEGES_CHANNEL,
        format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level} | {message}",
    )

    logger.add(
        ERROR_LOG_DIR / "errors.log",
        level="ERROR",
        rotation="10 MB",
        retention="60 days",
        compression="zip",
        encoding="utf-8",
        enqueue=True,
        backtrace=DEV_MODE,
        diagnose=DEV_MODE,
        format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level} | {name}:{function}:{line} | {message}",
    )

    logger.add(
        PAYMENTS_LOG_DIR / "payments.log",
        level="INFO",
        rotation="1 month",
        retention="1 year",
        compression="zip",
        encoding="utf-8",
        enqueue=True,
        filter=lambda record: record["extra"].get("channel") == PAYMENTS_CHANNEL,
        format=("{time:YYYY-MM-DD HH:mm:ss.SSS} | {level} | {message}"),
    )

    logger.add(
        STRIPE_LOG_DIR / "stripe.log",
        level="INFO",
        rotation="1 month",
        retention="1 year",
        compression="zip",
        encoding="utf-8",
        enqueue=True,
        filter=lambda record: record["extra"].get("channel") == STRIPE_CHANNEL,
        format=("{time:YYYY-MM-DD HH:mm:ss.SSS} | {level} | {message}"),
    )
