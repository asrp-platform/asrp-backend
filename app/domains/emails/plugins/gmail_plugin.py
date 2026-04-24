from fastapi_mail import ConnectionConfig, FastMail, MessageSchema, MessageType
from loguru import logger

from app.core.config import settings
from app.domains.emails.common.abstract_plugin import EmailPlugin


class GmailPlugin(EmailPlugin):
    def __init__(self):
        self.config = ConnectionConfig(
            MAIL_USERNAME=settings.GMAIL_USERNAME,
            MAIL_PASSWORD=settings.GMAIL_PASSWORD,
            MAIL_FROM=settings.GMAIL_FROM,
            MAIL_PORT=settings.GMAIL_PORT,
            MAIL_SERVER=settings.GMAIL_SERVER,
            MAIL_STARTTLS=True,
            MAIL_SSL_TLS=False,
            USE_CREDENTIALS=True,
            VALIDATE_CERTS=True,
        )
        self.fast_mail = FastMail(self.config)

    async def send_email(
        self,
        to: str,
        subject: str,
        body: str,
        plain: bool = True,
    ):
        try:
            subtype = MessageType.plain if plain else MessageType.html
            message = MessageSchema(
                subject=subject,
                recipients=[to],
                body=body,
                subtype=subtype,
            )
            await self.fast_mail.send_message(message)
        except Exception as exc:
            logger.error("Failed to send confirmation email to {}", exc)
