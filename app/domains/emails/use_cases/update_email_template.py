from typing import Annotated

from fastapi import Depends

from app.core.database.base_transaction_manager import BaseTransactionManager
from app.domains.emails.services import EmailTemplateServiceDep
from app.domains.shared.transaction_managers import TransactionManagerDep
from app.domains.emails.models import EmailTemplate
from app.core.utils.permissions import check_permissions


class UpdateEmailTemplateUseCase:
    def __init__(
        self,
        transaction_manager: BaseTransactionManager,
        email_service: EmailTemplateServiceDep,
    ):
        self.__transaction_manager = transaction_manager
        self.__email_service = email_service

    async def execute(self, permissions: list, email_template_id: int, **kwargs) -> list[EmailTemplate]:
        check_permissions("email_templates.update", permissions)
        async with self.__transaction_manager:
            return await self.__email_service.update_email_template(email_template_id, **kwargs)


def get_use_case(
    transaction_manager: TransactionManagerDep,
    email_service: EmailTemplateServiceDep,
) -> UpdateEmailTemplateUseCase:
    return UpdateEmailTemplateUseCase(transaction_manager, email_service)


UpdateEmailTemplateUseCaseDep = Annotated[UpdateEmailTemplateUseCase, Depends(get_use_case)]
