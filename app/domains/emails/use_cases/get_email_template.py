from typing import Annotated

from fastapi import Depends

from app.core.database.base_transaction_manager import BaseTransactionManager
from app.core.utils.permissions import check_permissions
from app.domains.emails.models import EmailTemplate
from app.domains.emails.services import EmailTemplateServiceDep
from app.domains.shared.transaction_managers import TransactionManagerDep


class GetEmailTemplateUseCase:
    def __init__(
        self,
        transaction_manager: BaseTransactionManager,
        email_service: EmailTemplateServiceDep,
    ):
        self.__transaction_manager = transaction_manager
        self.__email_service = email_service

    async def execute(self, permissions: list, email_template_id: int) -> EmailTemplate:
        check_permissions("email_templates.view", permissions)
        async with self.__transaction_manager:
            return await self.__email_service.get_email_template_by_id(email_template_id)


def get_use_case(
    transaction_manager: TransactionManagerDep,
    email_service: EmailTemplateServiceDep,
) -> GetEmailTemplateUseCase:
    return GetEmailTemplateUseCase(transaction_manager, email_service)


GetEmailTemplateUseCaseDep = Annotated[GetEmailTemplateUseCase, Depends(get_use_case)]
