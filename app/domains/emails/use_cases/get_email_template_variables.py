from typing import Annotated

from fastapi import Depends

from app.core.utils.permissions import check_permissions
from app.domains.emails.common.variables import EmailTemplateVariableDTO
from app.domains.emails.services import EmailTemplateServiceDep


class GetEmailTemplateVariablesUseCase:
    def __init__(
        self,
        email_service: EmailTemplateServiceDep,
    ):
        self.__email_service = email_service

    def execute(self, permissions: list) -> list[EmailTemplateVariableDTO]:
        check_permissions("email_templates.view", permissions)
        return self.__email_service.get_email_template_variables()


def get_use_case(
    email_service: EmailTemplateServiceDep,
) -> GetEmailTemplateVariablesUseCase:
    return GetEmailTemplateVariablesUseCase(email_service)


GetEmailTemplateVariablesUseCaseDep = Annotated[GetEmailTemplateVariablesUseCase, Depends(get_use_case)]
