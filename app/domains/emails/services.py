from typing import Annotated, Type

from fastapi import Depends

from app.core.config import DEV_MODE
from app.domains.emails.common.abstract_provider import EmailProvider
from app.domains.emails.common.variables import VARIABLES_LIST, EmailTemplateVariableDTO
from app.domains.emails.exceptions import EmailTemplateNotFoundError
from app.domains.emails.models import EmailTemplate
from app.domains.shared.transaction_managers import TransactionManager, TransactionManagerDep


class EmailService:
    def __init__(self, provider: EmailProvider):
        self.provider = provider

    async def send_email(self, to: str, subject: str, body: str):
        await self.provider.send_email(to, subject, body)


class EmailTemplateService:
    def __init__(self, transaction_manager: TransactionManager):
        self.transaction_manager = transaction_manager

    async def get_email_templates(self) -> list[EmailTemplate]:
        return await self.transaction_manager.email_templates_repository.list()

    async def get_email_template_by_id(self, email_template_id: int) -> EmailTemplate:
        email_template = await self.transaction_manager.email_templates_repository.get_first_by_kwargs(id=email_template_id)

        if email_template is None:
            raise EmailTemplateNotFoundError("Email template with provided ID not found")

        return email_template

    async def create_email_template(self, **kwargs) -> EmailTemplate:
        return await self.transaction_manager.email_templates_repository.create(**kwargs)

    async def update_email_template(self, email_template_id: int, **kwargs) -> EmailTemplate:
        await self.get_email_template_by_id(email_template_id)
        return await self.transaction_manager.email_templates_repository.update(email_template_id, **kwargs)

    async def delete_email_template(self, email_template_id: int) -> None:
        await self.get_email_template_by_id(email_template_id)
        await self.transaction_manager.email_templates_repository.mark_as_deleted(email_template_id)

    @staticmethod
    def get_email_template_variables() -> list[EmailTemplateVariableDTO]:
        return VARIABLES_LIST


class MockEmailService(EmailService):
    async def send_email(self, to: str, subject: str, body: str) -> None:
        print(f"[MOCK EMAIL]\nTo: {to}\nSubject: {subject}\nBody: {body}\n")  # noqa: T201 mock print


def get_email_service(provider: Type[EmailProvider]) -> EmailService:
    provider_instance = provider()

    if DEV_MODE:
        return MockEmailService(provider_instance)

    return EmailService(provider_instance)


def get_email_template_service(transaction_manager: TransactionManagerDep) -> EmailTemplateService:
    return EmailTemplateService(transaction_manager)


EmailTemplateServiceDep = Annotated[EmailTemplateService, Depends(get_email_template_service)]
