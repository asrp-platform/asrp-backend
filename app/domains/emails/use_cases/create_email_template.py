from typing import Annotated

from fastapi import Depends

from app.core.database.base_transaction_manager import BaseTransactionManager
from app.core.utils.permissions import check_permissions
from app.domains.emails.models import EmailTemplate
from app.domains.emails.services import EmailTemplateServiceDep
from app.domains.shared.transaction_managers import TransactionManagerDep


class CreateEmailTemplateUseCase:
    def __init__(
        self,
        transaction_manager: BaseTransactionManager,
        email_service: EmailTemplateServiceDep,
    ):
        self.__transaction_manager = transaction_manager
        self.__email_service = email_service

    async def execute(self, permissions: list, **kwargs) -> EmailTemplate:
        check_permissions("email_templates.create", permissions)
        async with self.__transaction_manager:
            return await self.__email_service.create_email_template(**kwargs)


def get_use_case(
    transaction_manager: TransactionManagerDep,
    email_service: EmailTemplateServiceDep,
) -> CreateEmailTemplateUseCase:
    return CreateEmailTemplateUseCase(transaction_manager, email_service)


CreateEmailTemplateUseCaseDep = Annotated[CreateEmailTemplateUseCase, Depends(get_use_case)]
