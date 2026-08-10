from typing import Annotated

from fastapi import APIRouter, Depends, Path

from app.core.common.responses import NotAuthorizedResponses, PermissionsResponses
from app.domains.emails.schemas import (
    CreateEmailTemplateSchema,
    EmailTemplateVariablesSchema,
    UpdateEmailTemplateSchema,
    ViewEmailTemplateSchema,
)
from app.domains.emails.use_cases.create_email_template import CreateEmailTemplateUseCaseDep
from app.domains.emails.use_cases.delete_email_template import DeleteEmailTemplateUseCaseDep
from app.domains.emails.use_cases.get_email_template import GetEmailTemplateUseCaseDep
from app.domains.emails.use_cases.get_email_template_variables import GetEmailTemplateVariablesUseCaseDep
from app.domains.emails.use_cases.get_email_templates import GetEmailTemplatesUseCaseDep
from app.domains.emails.use_cases.update_email_template import UpdateEmailTemplateUseCaseDep
from app.domains.shared.deps import AdminPermissionsDep, get_admin_user


router = APIRouter(prefix="/email-templates", tags=["Admin: Email templates"], dependencies=[Depends(get_admin_user)])


class EmailTemplateResponses(PermissionsResponses, NotAuthorizedResponses):
    pass


class EmailTemplateByIdResponses(EmailTemplateResponses):
    NOT_FOUND = 404, "Email template with provided ID not found"


@router.get(
    "/variables",
    summary="Get available email template variables",
    responses=EmailTemplateResponses.responses,
)
async def get_email_template_variables(
    permissions: AdminPermissionsDep,
    use_case: GetEmailTemplateVariablesUseCaseDep,
) -> list[EmailTemplateVariablesSchema]:
    return use_case.execute(permissions)


@router.get(
    "",
    summary="Get all email templates",
    responses=EmailTemplateResponses.responses,
)
async def get_email_templates(
    permissions: AdminPermissionsDep,
    use_case: GetEmailTemplatesUseCaseDep
) -> list[ViewEmailTemplateSchema]:
    data, _ = await use_case.execute(permissions)
    return data


@router.get(
    "/{email_template_id}",
    summary="Get email template by ID",
    responses=EmailTemplateByIdResponses.responses,
)
async def get_email_template(
    email_template_id: Annotated[int, Path(...)],
    permissions: AdminPermissionsDep,
    use_case: GetEmailTemplateUseCaseDep
) -> ViewEmailTemplateSchema:
    return await use_case.execute(permissions, email_template_id)


@router.post(
    "",
    status_code=201,
    summary="Create email template",
    responses=EmailTemplateResponses.responses,
)
async def create_email_template(
    permissions: AdminPermissionsDep,
    data: CreateEmailTemplateSchema,
    use_case: CreateEmailTemplateUseCaseDep
) -> ViewEmailTemplateSchema:
    return await use_case.execute(permissions, **data.model_dump())


@router.patch(
    "/{email_template_id}",
    summary="Update email template",
    responses=EmailTemplateByIdResponses.responses,
)
async def update_email_template(
    email_template_id: Annotated[int, Path(...)],
    permissions: AdminPermissionsDep,
    data: UpdateEmailTemplateSchema,
    use_case: UpdateEmailTemplateUseCaseDep
) -> ViewEmailTemplateSchema:
    return await use_case.execute(permissions, email_template_id, **data.model_dump(exclude_unset=True))


@router.delete(
    "/{email_template_id}",
    status_code=204,
    summary="Delete email template",
    responses=EmailTemplateByIdResponses.responses,
)
async def delete_email_template(
    email_template_id: Annotated[int, Path(...)],
    permissions: AdminPermissionsDep,
    use_case: DeleteEmailTemplateUseCaseDep
) -> None:
    return await use_case.execute(permissions, email_template_id)
