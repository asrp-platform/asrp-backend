from typing import Type

from app.core.config import DEV_MODE
from app.domains.emails.common.abstract_provider import EmailProvider


class EmailService:
    def __init__(self, provider: EmailProvider):
        self.provider = provider

    async def send_email(self, to: str, subject: str, body: str):
        await self.provider.send_email(to, subject, body)


class MockEmailService(EmailService):
    async def send_email(self, to: str, subject: str, body: str) -> None:
        print(f"[MOCK EMAIL]\nTo: {to}\nSubject: {subject}\nBody: {body}\n")  # noqa: T201 mock print


def get_email_service(provider: Type[EmailProvider]) -> EmailService:
    provider_instance = provider()

    if DEV_MODE:
        return MockEmailService(provider_instance)

    return EmailService(provider_instance)
